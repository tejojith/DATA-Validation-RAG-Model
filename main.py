from new_codebase_rag import CodebaseRAG
from rag_config import check_for_file

# PROJECT_PATH, 
DB_PATH = check_for_file()

rag = CodebaseRAG(DB_PATH)

# Configure databases
source_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',
    'database': 'source_db'
}

target_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',
    'database': 'target_db'
}

rag.configure_databases(source_config, target_config)


rag.create_embeddings_and_store()   
rag.query_rag_system()
