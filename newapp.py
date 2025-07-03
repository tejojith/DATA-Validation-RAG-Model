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

# Global variables to maintain state across requests
rag_instance = None
DB_PATH = None

def initialize_rag():
    """
    Initializes the CodebaseRAG instance.
    This function ensures that a single RAG instance is used across all requests
    and attempts to load the vector database if it hasn't been loaded yet.
    """
    global rag_instance, DB_PATH
    if rag_instance is None:
        # Determine the FAISS DB path. This might involve user interaction
        # on the console if no existing DB is found.
        DB_PATH = check_for_file()
        rag_instance = CodebaseRAG(DB_PATH)
        # Attempt to load the vector DB immediately upon initialization
        # if it's not already loaded. This prepares the RAG for queries.
        try:
            if rag_instance.vector_db is None:
                rag_instance.load_vector_db()
        except Exception as e:
            print(f"Warning: Could not load existing vector DB on initialization: {e}")
            # Do not re-raise, allow the app to start even if DB load fails initially
            # Embeddings can be created later via the /api/create-embeddings endpoint.
    return rag_instance

@app.route('/')
def landing():
    """Renders the landing page for database configuration and embedding creation."""
    return render_template('landing.html')

@app.route('/query')
def query():
    """Renders the query page for submitting validation queries."""
    return render_template('query_page.html')

@app.route('/scripts')
def scripts():
    """Renders the scripts page for managing and executing generated scripts."""
    return render_template('scripts.html')

@app.route('/api/configure-databases', methods=['POST'])
def configure_databases():
    """
    Configures the source and target databases for the RAG system.
    Requires source_config and optionally target_config in the request JSON.
    """
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
        # Log the full traceback for debugging purposes
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-embeddings', methods=['POST'])
def create_embeddings():
    """
    Creates and stores embeddings for the RAG system.
    Requires database configuration to be set first.
    """
    try:
        rag = initialize_rag()
        if not rag.source_db_config:
            return jsonify({'error': 'Database configuration required first'}), 400
        
        # Check if embeddings are already created in the current RAG instance
        if rag.vector_db is not None:
            return jsonify({'message': 'Embeddings already created and loaded.'})

        rag.create_embeddings_and_store()
        return jsonify({'message': 'Embeddings created and stored successfully!'})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/query', methods=['POST'])
def query_rag():
    """
    Processes a user query using the RAG system.
    Requires the query in the request JSON and embeddings to be created.
    """
    try:
        data = request.json
        query = data.get('query')
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        rag = initialize_rag()
        # Ensure the vector database is loaded before attempting to query
        if not rag.vector_db:
            # If embeddings were not loaded at initialization, try to load them now
            try:
                rag.load_vector_db()
            except Exception as e:
                return jsonify({'error': f'Embeddings not found or failed to load: {e}. Please create embeddings first.'}), 400
        
        # Import necessary components for query processing (if not already imported globally)
        from langchain_ollama.llms import OllamaLLM
        from langchain.chains import RetrievalQA
        # Assuming PROMPT_TEMPLATES is defined in a 'prompts' module or similar
        # For this example, I'll use a placeholder, you might need to adjust based on your actual prompts.
        # from prompts import PROMPT_TEMPLATES # Uncomment if you have this module
        
        # Placeholder for PROMPT_TEMPLATES if not using a separate module
        PROMPT_TEMPLATES = {
            "validation": "You are a helpful assistant. Based on the following context, provide a SQL query or validation logic for the question: {question}\n\nContext:\n{context}",
            "comparison": "You are an expert in data validation. Compare the following source and target database schemas/data based on the question. Provide SQL queries or validation steps to perform the comparison.\n\nSource Context:\n{source_context}\n\nTarget Context:\n{target_context}\n\nQuestion: {question}",
            "default": "You are a helpful assistant. Based on the following context, answer the question: {question}\n\nContext:\n{context}"
        }
        
        import time
        
        # Classify query and select LLM model (logic from new_codebase_rag.py)
        query_type = rag.classify_query(query)
        llm_model = rag.select_llm(query)
        
        retriever = rag.vector_db.as_retriever()
        llm = OllamaLLM(
            model=llm_model,
            temperature=0.1,
            top_k=10,
            repeat_penalty=1.1
        )
        
        start_time = time.time()
        
        if query_type == "comparison" and rag.target_db_config:
            # Fetch relevant documents for source and target
            all_docs = rag.vector_db.similarity_search(query, k=6) # Increased k for more context
            source_docs = [doc for doc in all_docs if doc.metadata.get("source") == "source_db"]
            target_docs = [doc for doc in all_docs if doc.metadata.get("source") == "target_db"]
            
            source_context = "\n".join([doc.page_content for doc in source_docs[:3]])
            target_context = "\n".join([doc.page_content for doc in target_docs[:3]])
            
            prompt = PROMPT_TEMPLATES[query_type].format(
                source_context=source_context,
                target_context=target_context,
                question=query
            )
            
            result = {"result": llm.invoke(prompt)}
        else:
            qa = RetrievalQA.from_chain_type(
                llm=llm,
                retriever=retriever,
                return_source_documents=True,
                chain_type_kwargs={
                    "prompt": PROMPT_TEMPLATES.get(query_type, PROMPT_TEMPLATES["default"])
                }
            )
            result = qa.invoke({"query": query}) # Use invoke with a dictionary for RetrievalQA
        
        end_time = time.time()
        
        # The 'result' structure from RetrievalQA.invoke is usually {'query': ..., 'result': ..., 'source_documents': ...}
        # The 'result' from llm.invoke is just the string.
        # Normalize the output to always have a 'result' key for the answer.
        answer_content = result.get("result", result) if isinstance(result, dict) else result
        
        return jsonify({
            'answer': answer_content,
            'query_type': query_type,
            'llm_model': llm_model,
            'processing_time': round(end_time - start_time, 2)
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/save-script', methods=['POST'])
def save_script():
    """
    Saves the generated SQL script to the 'results' directory.
    Extracts SQL content from the answer and saves it to a .sql file.
    """
    try:
        data = request.json
        answer = data.get('answer')
        query_type = data.get('query_type', 'validation')
        filename_prefix = data.get('filename', f'validation_{query_type}')
        
        if not answer:
            return jsonify({'error': 'Answer content is required'}), 400
        
        # Ensure results directory exists
        os.makedirs('results', exist_ok=True)
        
        # Extract SQL code from answer (robustly handle different markdown formats)
        content = answer.strip()
        if '```sql' in content:
            content = content.split('```sql', 1)[1].split('```', 1)[0].strip()
        elif '```' in content:
            content = content.split('```', 1)[1].split('```', 1)[0].strip()
        
        # Generate a unique filename to avoid overwriting
        counter = 0
        output_file = os.path.join('results', f"{filename_prefix}.sql")
        while os.path.exists(output_file):
            counter += 1
            output_file = os.path.join('results', f"{filename_prefix}_{counter}.sql")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        return jsonify({
            'message': f'Script saved to {os.path.basename(output_file)}',
            'filename': os.path.basename(output_file)
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/execute-script', methods=['POST'])
def execute_script():
    """
    Executes a specified SQL script against the source database.
    Returns the results of the execution.
    """
    try:
        data = request.json
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
        
        rag = initialize_rag()
        if not rag.source_db_config:
            return jsonify({'error': 'Database configuration required'}), 400
        
        # The ExecuteOutput class is designed to handle script execution
        executor = ExecuteOutput(script_filename=os.path.join('results', filename))
        
        # Capture execution results by temporarily overriding print or collecting them
        # For a web API, it's better to modify execute_final to return results
        # rather than printing. Assuming execute_final can return a list of results.
        
        # The original execute_output.py's execute_final prints.
        # We need to adapt it to return results for the API.
        # For now, I'll replicate the logic here to capture results directly.
        from connect_alchemy import MySQLConnection
        import sqlparse
        
        results = []
        conn = None # Initialize conn to None
        try:
            conn = MySQLConnection(**rag.source_db_config)
            script_path = os.path.join('results', filename)
            
            if not os.path.exists(script_path):
                return jsonify({'error': f'Script file not found: {filename}'}), 404

            with open(script_path, 'r') as file:
                script_content = file.read()
            
            statements = sqlparse.split(script_content)
            
            for stmt in statements:
                cleaned = stmt.strip()
                if cleaned:
                    try:
                        # Ensure connection is active before executing
                        if not conn.is_connected():
                            conn.connect() 
                        
                        result_df = conn.execute_query(cleaned)
                        if result_df is not None and not result_df.empty:
                            results.append({
                                'query': cleaned,
                                'result': result_df.to_dict('records'), # Convert DataFrame to list of dicts
                                'row_count': len(result_df)
                            })
                        else:
                            results.append({
                                'query': cleaned,
                                'result': 'Query executed successfully with no rows returned.',
                                'row_count': 0
                            })
                    except Exception as e:
                        results.append({
                            'query': cleaned,
                            'error': str(e)
                        })
        finally:
            if conn and conn.is_connected():
                conn.close()
        
        return jsonify({
            'message': 'Script executed successfully',
            'results': results
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-connection', methods=['POST'])
def test_connection():
    """
    Tests the database connection with the provided configuration.
    """
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
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-script/<filename>')
def download_script(filename):
    """
    Downloads a specified script file from the 'results' directory.
    """
    try:
        return send_file(
            os.path.join('results', filename),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 404

@app.route('/api/list-scripts')
def list_scripts():
    """
    Lists all generated SQL script files in the 'results' directory.
    """
    try:
        results_dir = 'results'
        if not os.path.exists(results_dir):
            return jsonify({'scripts': []})
        
        scripts = [f for f in os.listdir(results_dir) if f.endswith('.sql')]
        return jsonify({'scripts': scripts})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

