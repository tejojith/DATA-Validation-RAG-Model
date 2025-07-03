from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import os
import json
from new_codebase_rag import CodebaseRAG
from rag_config import check_for_file
from execute_output import ExecuteOutput
import traceback

app = Flask(__name__)
CORS(app)

# Global variables
rag_instance = None
DB_PATH = None
embeddings_created = False

def initialize_rag():
    global rag_instance, DB_PATH
    if rag_instance is None:
        DB_PATH = check_for_file()
        rag_instance = CodebaseRAG(DB_PATH)
    return rag_instance

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/query')
def query():
    return render_template('query_page.html')

@app.route('/scripts')
def scripts():
    return render_template('scripts.html')

@app.route('/api/configure-databases', methods=['POST'])
def configure_databases():
    try:
        data = request.json
        source_config = data.get('source_config')
        target_config = data.get('target_config')
        
        if not source_config:
            return jsonify({'error': 'Source database configuration is required'}), 400
        
        rag = initialize_rag()
        rag.configure_databases(source_config, target_config)
        
        return jsonify({'message': 'Database configurations set successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-embeddings', methods=['POST'])
def create_embeddings():
    global embeddings_created
    try:
        data = request.json
        transformation_path = data.get('transformation_path')
        
        rag = initialize_rag()
        if not rag.source_db_config:
            return jsonify({'error': 'Database configuration required first'}), 400
        
        # Set transformation logic if provided
        if transformation_path and os.path.exists(transformation_path):
            rag.extract_transformation_logic(transformation_path)
        
        # Create embeddings and store
        rag.create_embeddings_and_store()
        embeddings_created = True
        
        return jsonify({
            'message': 'Embeddings created and stored successfully',
            'embeddings_ready': True
        })
    except Exception as e:
        print(f"Error creating embeddings: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/embeddings-status')
def embeddings_status():
    global embeddings_created
    return jsonify({'embeddings_ready': embeddings_created})

@app.route('/api/query', methods=['POST'])
def query_rag():
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
        from new_prompt import VALIDATION_PROMPT
        import time
        
        retriever = rag.vector_db.as_retriever(
            search_kwargs={"k": 3, "fetch_k": 6, "score_threshold": 0.7}
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
        llm_chain = LLMChain(llm=llm, prompt=VALIDATION_PROMPT)
        
        # Execute query
        result = llm_chain.invoke({
            "context": context,
            "source_db": rag.source_db_config.get('database', 'source_db') if rag.source_db_config else 'source_db',
            "target_db": rag.target_db_config.get('database', 'target_db') if rag.target_db_config else 'target_db',
            "transformation_logic": transformation_logic,
            "query": query
        })
        
        end_time = time.time()
        
        return jsonify({
            'answer': result["text"],
            'llm_model': model_name,
            'processing_time': round(end_time - start_time, 2)
        })
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

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
        
        output_file = f"results/{filename}"
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        return jsonify({
            'message': f'Script saved to {output_file}',
            'filename': filename
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
        script_path = os.path.join('results', filename)
        if not os.path.exists(script_path):
            return jsonify({'error': f'Script file {filename} not found'}), 404
        
        executor = ExecuteOutput(script_filename=filename)
        results = executor.execute_and_capture_results(rag.source_db_config)
        
        return jsonify({
            'message': 'Script executed successfully',
            'results': results
        })
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/test-connection', methods=['POST'])
def test_connection():
    try:
        data = request.json
        config = data.get('config')
        
        if not config:
            return jsonify({'error': 'Database configuration is required'}), 400
        
        from connect_alchemy import MySQLConnection
        conn = MySQLConnection(**config)
        
        if conn.connect():
            conn.close()
            return jsonify({'message': 'Connection successful'})
        else:
            return jsonify({'error': 'Connection failed'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

@app.route('/api/list-scripts')
def list_scripts():
    try:
        results_dir = 'results'
        if not os.path.exists(results_dir):
            return jsonify({'scripts': []})
        
        scripts = [f for f in os.listdir(results_dir) if f.endswith('.sql')]
        return jsonify({'scripts': scripts})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Add missing utility functions for the frontend
def showAlert(message, type='success'):
    return f'<div class="alert alert-{type}">{message}</div>'

def showLoading(show):
    return f'<div class="loading" style="display: {"block" if show else "none"}"><div class="spinner"></div><p>Processing...</p></div>'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)