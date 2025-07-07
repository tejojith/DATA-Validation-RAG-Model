from flask import Flask, request, jsonify, render_template, send_file, session, send_from_directory
from flask_cors import CORS
import os
import json
from new_codebase_rag import CodebaseRAG
from rag_config import check_for_file
from execute_output import ExecuteOutput
import traceback
from utils.github import push_file_and_open_pr
from datetime import datetime
from werkzeug.utils import secure_filename
import shutil
import tempfile
import subprocess

import configparser
config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
config.read(config_path)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Add secret key for session management
CORS(app)

# Global variables
rag_instance = None
DB_PATH = None
embeddings_created = False
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'sql', 'txt', 'json', 'csv'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

ALLURE_RESULTS_DIR = 'allure-results'   # raw JSON produced by pytest
ALLURE_REPORT_DIR = 'allure-report'     # generated HTML dashboard

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Store query results globally for dashboard access
query_results_store = []

for _dir in (UPLOAD_FOLDER, ALLURE_RESULTS_DIR, ALLURE_REPORT_DIR):
    os.makedirs(_dir, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def initialize_rag():
    global rag_instance, DB_PATH
    if rag_instance is None:
        DB_PATH = check_for_file()
        rag_instance = CodebaseRAG(DB_PATH)
    return rag_instance

def generate_allure_report(force: bool = False):
    """Generate/update Allure HTML report (ALLURE_REPORT_DIR) from ALLURE_RESULTS_DIR.

    Parameters
    ----------
    force : bool
        If True, force regeneration even if results are unchanged.
    """
    try:
        # If report already exists and not forced, skip regeneration
        if not force and os.path.exists(os.path.join(ALLURE_REPORT_DIR, 'index.html')):
            return "Allure report already exists - skipped regeneration."

        # Call Allure CLI
        subprocess.run([
            'allure', 'generate', ALLURE_RESULTS_DIR,
            '-o', ALLURE_REPORT_DIR,
            '--clean'
        ], check=True)
        return "Allure report generated successfully."
    except FileNotFoundError:
        raise RuntimeError("Allure CLI not found in PATH. Install Allure and ensure the 'allure' command is available.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Allure generation failed: {e}")

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/query')
def query():
    return render_template('query_page.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')




source_db_config = {
    'host': config.get('source_db', 'host', fallback='localhost'),
    'port': config.getint('source_db', 'port', fallback=3306),
    'user': config.get('source_db', 'user', fallback='root'),
    'password': config.get('source_db', 'password', fallback='password'),
    'database': config.get('source_db', 'database', fallback='source_db')
}
target_db_config = {
    'host': config.get('target_db', 'host', fallback='localhost'),
    'port': config.getint('target_db', 'port', fallback=3306),
    'user': config.get('target_db', 'user', fallback='root'),
    'password': config.get('target_db', 'password', fallback='password'),
    'database': config.get('target_db', 'database', fallback='target_db')
}

############################################################
# 🏷️ Allure static file serving
############################################################

@app.route('/allure-report/')
def allure_root():
    """Serve the Allure dashboard's landing page."""
    index_path = os.path.join(ALLURE_REPORT_DIR, 'index.html')

    # Auto‑generate the report if it doesn't exist
    if not os.path.exists(index_path):
        try:
            generate_allure_report(force=False)
        except RuntimeError as e:
            return f"<h2>Allure report unavailable</h2><p>{e}</p>", 500

    return send_file(index_path)


@app.route('/allure-report/<path:resource>')
def allure_static(resource):
    """Serve JS/CSS/images used by the Allure dashboard."""
    full_path = os.path.join(ALLURE_REPORT_DIR, resource)
    if not os.path.exists(full_path):
        return "Resource not found", 404
    return send_from_directory(ALLURE_REPORT_DIR, resource)


@app.route('/api/generate-allure', methods=['POST'])
def api_generate_allure():
    """REST endpoint to (re)generate the Allure report on‑demand."""
    try:
        message = generate_allure_report(force=True)
        return jsonify({'message': message})
    except RuntimeError as exc:
        return jsonify({'error': str(exc)}), 500




rag = initialize_rag()
rag.configure_databases(source_db_config, target_db_config)

@app.route('/api/create-embeddings', methods=['POST'])
def create_embeddings():
    global embeddings_created, uploaded_files_info
    
    try:
        # Check if files were uploaded
        if 'files' not in request.files:
            return jsonify({'error': 'No files uploaded'}), 400
        
        files = request.files.getlist('files')
        
        if not files or all(file.filename == '' for file in files):
            return jsonify({'error': 'No files selected'}), 400
        
        # Clear previous uploads
        uploaded_files_info = []
        
        # Process and save uploaded files
        saved_files = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to avoid conflicts
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                saved_files.append(filepath)
                
                # Store file info
                uploaded_files_info.append({
                    'filename': filename,
                    'original_name': file.filename,
                    'filepath': filepath,
                    'size': os.path.getsize(filepath)
                })
        
        if not saved_files:
            return jsonify({'error': 'No valid files uploaded'}), 400
        
        # Initialize RAG system
        rag = initialize_rag()
        
        # Process the uploaded files to create embeddings
        try:
            # Read and process each file
            documents = []
            for filepath in saved_files:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Add metadata about the file
                        doc_with_metadata = {
                            'content': content,
                            'filename': os.path.basename(filepath),
                            'filepath': filepath
                        }
                        documents.append(doc_with_metadata)
                except Exception as e:
                    print(f"Error reading file {filepath}: {str(e)}")
                    # Try with different encoding
                    try:
                        with open(filepath, 'r', encoding='latin-1') as f:
                            content = f.read()
                            doc_with_metadata = {
                                'content': content,
                                'filename': os.path.basename(filepath),
                                'filepath': filepath
                            }
                            documents.append(doc_with_metadata)
                    except Exception as e2:
                        print(f"Error reading file {filepath} with latin-1: {str(e2)}")
                        continue
            
            if not documents:
                return jsonify({'error': 'No readable documents found'}), 400
            
            # Create embeddings from the documents
            temp_dir = tempfile.mkdtemp()
            try:
                # Copy files to temp directory
                for doc in documents:
                    temp_file_path = os.path.join(temp_dir, doc['filename'])
                    shutil.copy2(doc['filepath'], temp_file_path)
                
                # Set the transformation path to the temp directory
                #hard coded the transformation path because need more time to identify the transformation script
                rag.transformation_path = r'D:\DATA Validation\Schemas\transformation scripts.sql'
                
                # Create embeddings
                rag.create_embeddings_and_store()
                embeddings_created = True
                
                return jsonify({
                    'message': 'Embeddings created successfully',
                    'embeddings_ready': True,
                    'files_processed': len(documents),
                    'file_info': uploaded_files_info
                })
                
            finally:
                # Clean up temp directory
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            print(f"Error creating embeddings: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                'error': f'Error creating embeddings: {str(e)}',
                'traceback': traceback.format_exc()
            }), 500
            
    except Exception as e:
        print(f"General error in create_embeddings: {str(e)}")
        return jsonify({
            'error': f'Server error: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/embeddings-status')
def embeddings_status():
    global embeddings_created
    return jsonify({'embeddings_ready': embeddings_created})

@app.route('/api/query', methods=['POST'])
def query_rag():
    global query_results_store
    try:
        data = request.json
        query = data.get('query')
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        rag = initialize_rag()
        if not rag.vector_db:
            try:
                rag.load_vector_db()
            except Exception as e:
                return jsonify({'error': 'Vector database not found. Please create embeddings first.'}), 400
        
        # Get query classification and LLM model
        model_name, params = rag.select_llm_optimized(query)
        
        # Process the query
        from langchain_ollama.llms import OllamaLLM
        from langchain.chains import LLMChain
        from new_prompt import NEW_PROMPT
        import time
        
        retriever = rag.vector_db.as_retriever(
            search_type="mmr",  # Maximum Marginal Relevance for diversity
            search_kwargs={
                "k": 3,
                "fetch_k": 6,
                "lambda_mult": 0.7,  # Balance between relevance and diversity
                "score_threshold": 0.7  # Lower threshold for more inclusive results
            }
        )
        
        llm = OllamaLLM(model=model_name, **params)
        
        start_time = time.time()
        
        # Get transformation logic if available
        if hasattr(rag, 'transformation_path') and rag.transformation_path:
            transformation_logic = rag.extract_transformation_logic(rag.transformation_path)
            if isinstance(transformation_logic, list):
                transformation_logic = "\n".join(transformation_logic)
        else:
            transformation_logic = "No transformation logic provided"
        
        # Retrieve relevant documents
        retrieved_docs = retriever.invoke(query)
        context = "\n".join(doc.page_content for doc in retrieved_docs)
        
        # Create LLM chain
        llm_chain = LLMChain(llm=llm, prompt = NEW_PROMPT)
        
        # Execute query
        result = llm_chain.invoke({
            "context": context,
            "source_db": rag.source_db_config.get('database', 'source_db') if rag.source_db_config else 'source_db',
            "target_db": rag.target_db_config.get('database', 'target_db') if rag.target_db_config else 'target_db',
            "transformation_logic": transformation_logic,
            "query": query
        })
        print(result)
        end_time = time.time()
        
        # Store query result for dashboard
        query_result = {
            'id': len(query_results_store) + 1,
            'query': query,
            'answer': result["text"],
            'llm_model': model_name,
            'processing_time': round(end_time - start_time, 2),
            'timestamp': datetime.now().isoformat(),
            'status': 'completed'
        }
        
        query_results_store.append(query_result)
        
        return jsonify({
            'answer': result["text"],
            'llm_model': model_name,
            'processing_time': round(end_time - start_time, 2),
            'dashboard_url': '/dashboard'  # Provide dashboard URL for frontend
        })
    except Exception as e:
        # Store error result for dashboard
        error_result = {
            'id': len(query_results_store) + 1,
            'query': query if 'query' in locals() else 'Unknown query',
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'status': 'error'
        }
        query_results_store.append(error_result)
        
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/query-results')
def get_query_results():
    """API endpoint to get query results for dashboard"""
    global query_results_store
    return jsonify(query_results_store)

@app.route('/api/clear-results', methods=['POST'])
def clear_results():
    """API endpoint to clear query results"""
    global query_results_store
    query_results_store = []
    return jsonify({'message': 'Results cleared successfully'})

@app.route('/api/execute-sql', methods=['POST'])
def execute_sql():
    """API endpoint to execute SQL queries extracted from RAG responses"""
    try:
        data = request.json
        sql_query = data.get('sql_query')
        result_id = data.get('result_id')
        
        if not sql_query:
            return jsonify({'error': 'SQL query is required'}), 400
        
        rag = initialize_rag()
        if not rag.source_db_config:
            return jsonify({'error': 'Database configuration required'}), 400
        
        # Execute SQL query using ExecuteOutput
        try:
            # Create a temporary SQL file
            temp_sql_file = tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False)
            temp_sql_file.write(sql_query)
            temp_sql_file.close()
            
            # Execute the query
            executor = ExecuteOutput(script_filename=temp_sql_file.name)
            execution_results = executor.execute_and_capture_results(rag.source_db_config)
            
            # Clean up temp file
            os.unlink(temp_sql_file.name)
            
            # Update the stored query result with execution results
            if result_id:
                for result in query_results_store:
                    if result['id'] == result_id:
                        result['execution_results'] = execution_results
                        result['executed'] = True
                        break
            
            return jsonify({
                'message': 'SQL query executed successfully',
                'results': execution_results
            })
            
        except Exception as e:
            return jsonify({'error': f'SQL execution failed: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/save-script', methods=['POST'])
def save_script():
    try:
        data = request.json
        answer = data.get('answer')
        query_type = data.get('query_type', 'validation')
        filename = data.get('filename', f'validation_{query_type}')
        
        if not answer:
            return jsonify({'error': 'Answer content is required'}), 400
        
        # Ensure results directory exists
        os.makedirs('results', exist_ok=True)
        
        # Extract SQL code from answer
        content = extract_sql_from_answer(answer)
        
        # Ensure filename has .sql extension
        if not filename.endswith('.sql'):
            filename = f"{filename}.sql"
        
        output_file = r"D:\New folder\scripts\results\{}".format(filename)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        try:
            pr_url = push_file_and_open_pr(
                local_repo_path = r"D:\New folder\scripts",
                new_file        = output_file,
                pr_title        = f"Validation script: {filename}",
                pr_body         = f"Auto - generated by RAG assistant at {datetime.utcnow()} UTC."
            )
        except Exception as gh_err:
            return jsonify({'error': f'GitHub push/PR failed: {gh_err}'}), 500

        return jsonify({
            'message' : f'Script saved and pushed to GitHub ({pr_url})',
            'filename': filename,
            'pr_url'  : pr_url
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def extract_sql_from_answer(answer):
    """Extract SQL code from the answer text"""
    # Try to find SQL code blocks
    if '```sql' in answer:
        # Multiple SQL blocks
        sql_blocks = []
        parts = answer.split('```sql')
        for part in parts[1:]:  # Skip first part (before first ```sql)
            if '```' in part:
                sql_block = part.split('```')[0].strip()
                if sql_block:
                    sql_blocks.append(sql_block)
        if sql_blocks:
            return '\n\n'.join(sql_blocks)
    
    # Try generic code blocks
    elif '```' in answer:
        parts = answer.split('```')
        for i in range(1, len(parts), 2):  # Get odd-indexed parts (code blocks)
            block = parts[i].strip()
            # Check if it looks like SQL
            if any(keyword in block.upper() for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER']):
                return block
    
    # If no code blocks found, return the whole answer
    return answer.strip()

@app.route('/api/execute-script', methods=['POST'])
def execute_script():
    try:
        data = request.json
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
        
        rag = initialize_rag()
        if not rag.source_db_config:
            return jsonify({'error': 'Database configuration required'}), 400
        
        # Execute script using ExecuteOutput
        script_path = os.path.join(r'D:\New folder\scripts\results', filename)
        if not os.path.exists(script_path):
            return jsonify({'error': f'Script file {filename} not found'}), 404
        
        executor = ExecuteOutput(script_filename=script_path)
        results = executor.execute_and_capture_results(rag.source_db_config)
        
        return jsonify({
            'message': 'Script executed successfully',
            'results': results
        })
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/download-script/<filename>')
def download_script(filename):
    try:
        return send_file(
            os.path.join('results', filename),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 404

def showAlert(message, type='success'):
    return f'<div class="alert alert-{type}">{message}</div>'

def showLoading(show):
    return f'<div class="loading" style="display: {"block" if show else "none"}"><div class="spinner"></div><p>Processing...</p></div>'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)