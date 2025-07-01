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
    try:
        rag = initialize_rag()
        if not rag.source_db_config:
            return jsonify({'error': 'Database configuration required first'}), 400
        
        rag.create_embeddings_and_store()
        return jsonify({'message': 'Embeddings created and stored successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/query', methods=['POST'])
def query_rag():
    try:
        data = request.json
        query = data.get('query')
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        rag = initialize_rag()
        if not rag.vector_db:
            rag.load_vector_db()
        
        # Get query classification and LLM model
        query_type = rag.classify_query(query)
        llm_model = rag.select_llm(query)
        
        # Process the query (simplified version)
        from langchain_ollama.llms import OllamaLLM
        from langchain.chains import RetrievalQA
        from prompts import PROMPT_TEMPLATES
        import time
        
        retriever = rag.vector_db.as_retriever()
        llm = OllamaLLM(
            model=llm_model,
            temperature=0.1,
            top_k=10,
            repeat_penalty=1.1
        )
        
        start_time = time.time()
        
        if query_type == "comparison" and rag.target_db_config:
            all_docs = rag.vector_db.similarity_search(query, k=6)
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
                    "prompt": PROMPT_TEMPLATES[query_type]
                }
            )
            result = qa(query)
        
        end_time = time.time()
        
        return jsonify({
            'answer': result["result"],
            'query_type': query_type,
            'llm_model': llm_model,
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
        if '```sql' in answer:
            content = answer.split('```sql')[1].split('```')[0].strip()
        elif '```' in answer:
            content = answer.split('```')[1].split('```')[0].strip()
        else:
            content = answer.strip()
        
        output_file = f"results/{filename}.sql"
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        return jsonify({
            'message': f'Script saved to {output_file}',
            'filename': f'{filename}.sql'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        
        executor = ExecuteOutput(script_filename=filename)
        
        # Capture execution results
        results = []
        
        # Override the execute_final method to capture results
        from connect_alchemy import MySQLConnection
        import sqlparse
        
        conn = MySQLConnection(**rag.source_db_config)
        try:
            script_path = os.path.join('results', filename)
            with open(script_path, 'r') as file:
                script_content = file.read()
            
            statements = sqlparse.split(script_content)
            
            for stmt in statements:
                cleaned = stmt.strip()
                if cleaned:
                    try:
                        result = conn.execute_query(cleaned)
                        if result is not None and not result.empty:
                            results.append({
                                'query': cleaned,
                                'result': result.to_dict('records'),
                                'row_count': len(result)
                            })
                        else:
                            results.append({
                                'query': cleaned,
                                'result': 'Query executed successfully',
                                'row_count': 0
                            })
                    except Exception as e:
                        results.append({
                            'query': cleaned,
                            'error': str(e)
                        })
        finally:
            conn.close()
        
        return jsonify({
            'message': 'Script executed successfully',
            'results': results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)