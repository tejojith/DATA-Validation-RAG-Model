import os
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader
from langchain.chains import RetrievalQA
from langchain_community.document_loaders import TextLoader
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_ollama.llms import OllamaLLM
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from multiprocessing import Pool
from langchain_community.document_loaders import (TextLoader, PythonLoader, 
                                                        JSONLoader, BSHTMLLoader)
import time
from langchain.prompts import PromptTemplate
from chunking import EnhancedChunker
from connector_sql import MySQLConnection
from typing import Dict, List, Optional
import pandas as pd
from prompts import PROMPT_TEMPLATES

class CodebaseRAG:
    def __init__(self, project_path: str, db_path: str):
        self.project_path = project_path
        self.db_path = db_path
        self.embed_model = "nomic-embed-text"  # or mxbai-embed-large for code
        self.embedding = OllamaEmbeddings(model=self.embed_model)
        self.chunker = EnhancedChunker(self.embedding)
        self.vector_db = None
        self.source_db_config = None
        self.target_db_config = None

    def configure_databases(self, source_config: Dict, target_config: Optional[Dict] = None):
        self.source_db_config = source_config
        self.target_db_config = target_config

    def extract_schema_info(self, connection_config: Dict) -> List[Dict]:
        schema_info = []
        
        with MySQLConnection(**connection_config) as conn:
            # Get tables
            tables_df = conn.execute_query("SHOW TABLES")
            if tables_df is None:
                return schema_info
                
            for _, row in tables_df.iterrows():
                table_name = row.iloc[0]
                
                # Get columns
                columns_df = conn.execute_query(f"DESCRIBE {table_name}")
                
                # Get foreign keys
                fks_df = conn.execute_query(f"""
                    SELECT COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = '{table_name}' 
                    AND REFERENCED_TABLE_NAME IS NOT NULL
                """)
                
                schema_info.append({
                    'table_name': table_name,
                    'columns': columns_df.to_dict('records') if columns_df is not None else [],
                    'foreign_keys': fks_df.to_dict('records') if fks_df is not None else []
                })
                    
        return schema_info

    def profile_data(self, connection_config: Dict) -> List[Dict]:
        profile_info = []
        
        with MySQLConnection(**connection_config) as conn:
            tables_df = conn.execute_query("SHOW TABLES")
            if tables_df is None:
                return profile_info
                
            for _, table_row in tables_df.iterrows():
                table_name = table_row.iloc[0]
                
                # Basic stats
                count_df = conn.execute_query(f"SELECT COUNT(*) as cnt FROM {table_name}")
                row_count = count_df.iloc[0]['cnt'] if count_df is not None else 0
                
                # Column profiles
                columns_df = conn.execute_query(f"DESCRIBE {table_name}")
                column_profiles = []
                
                if columns_df is not None:
                    for _, col_row in columns_df.iterrows():
                        col_name = col_row['Field']
                        col_type = col_row['Type']
                        
                        # Get sample values and NULL count
                        stats_df = conn.execute_query(f"""
                            SELECT 
                                SUM(CASE WHEN `{col_name}` IS NULL THEN 1 ELSE 0 END) as null_count,
                                COUNT(DISTINCT `{col_name}`) as distinct_count
                            FROM {table_name}
                        """)
                        
                        sample_df = conn.execute_query(f"""
                            SELECT `{col_name}` 
                            FROM {table_name} 
                            WHERE `{col_name}` IS NOT NULL
                            LIMIT 5
                        """)
                        
                        column_profiles.append({
                            'name': col_name,
                            'type': col_type,
                            'null_count': stats_df.iloc[0]['null_count'] if stats_df is not None else 0,
                            'distinct_count': stats_df.iloc[0]['distinct_count'] if stats_df is not None else 0,
                            'sample_values': sample_df[col_name].tolist() if sample_df is not None else []
                        })
                
                profile_info.append({
                    'table_name': table_name,
                    'row_count': row_count,
                    'columns': column_profiles
                })
                    
        return profile_info

    def create_embeddings_and_store(self):
        if not self.source_db_config:
            raise ValueError("Source database configuration is required")
            
        # Extract schema and profile data
        schema_info = self.extract_schema_info(self.source_db_config)
        profile_info = self.profile_data(self.source_db_config)
        
        # Prepare documents from schema and profile data
        from langchain.schema import Document
        documents = []
        
        # Add schema documents
        for table in schema_info:
            schema_text = f"Table: {table['table_name']}\nColumns:\n"
            for col in table['columns']:
                null_info = 'NULL' if col.get('Null', 'YES') == 'YES' else 'NOT NULL'
                schema_text += f"- {col.get('Field', '')}: {col.get('Type', '')} ({null_info})\n"
            
            if table['foreign_keys']:
                schema_text += "\nForeign Keys:\n"
                for fk in table['foreign_keys']:
                    schema_text += f"- {fk['COLUMN_NAME']} references {fk['REFERENCED_TABLE_NAME']}({fk['REFERENCED_COLUMN_NAME']})\n"
            
            documents.append(Document(
                page_content=schema_text,
                metadata={
                    'type': 'schema',
                    'table': table['table_name'],
                    'source': 'source_db'
                }
            ))
        
        # Add profile documents
        for profile in profile_info:
            profile_text = f"Table: {profile['table_name']}\nRow Count: {profile['row_count']}\nColumn Profiles:\n"
            for col in profile['columns']:
                profile_text += (f"- {col['name']} ({col['type']}): "
                            f"NULLs: {col['null_count']}, "
                            f"Distinct: {col['distinct_count']}, "
                            f"Samples: {col['sample_values']}\n")
            
            documents.append(Document(
                page_content=profile_text,
                metadata={
                    'type': 'profile',
                    'table': profile['table_name'],
                    'source': 'source_db'
                }
            ))
        
        # If target DB is configured, add its data too
        if self.target_db_config:
            target_schema = self.extract_schema_info(self.target_db_config)
            target_profile = self.profile_data(self.target_db_config)
            
            for table in target_schema:
                schema_text = f"[TARGET] Table: {table['table_name']}\nColumns:\n"
                for col in table['columns']:
                    null_info = 'NULL' if col.get('Null', 'YES') == 'YES' else 'NOT NULL'
                    schema_text += f"- {col.get('Field', '')}: {col.get('Type', '')} ({null_info})\n"
                
                documents.append(Document(
                    page_content=schema_text,
                    metadata={
                        'type': 'schema',
                        'table': table['table_name'],
                        'source': 'target_db'
                    }
                ))
            
            for profile in target_profile:
                profile_text = f"[TARGET] Table: {profile['table_name']}\nRow Count: {profile['row_count']}\n"
                for col in profile['columns']:
                    profile_text += (f"- {col['name']} ({col['type']}): "
                                f"NULLs: {col['null_count']}, "
                                f"Distinct: {col['distinct_count']}, "
                                f"Samples: {col['sample_values']}\n")
                
                documents.append(Document(
                    page_content=profile_text,
                    metadata={
                        'type': 'profile',
                        'table': profile['table_name'],
                        'source': 'target_db'
                    }
                ))
        
        # Chunk documents using enhanced chunker
        chunks = self.chunker.smart_chunk_documents(documents)
        
        # Create FAISS index
        self.vector_db = FAISS.from_documents(
            documents=chunks,
            embedding=self.embedding,
            distance_strategy="METRIC_INNER_PRODUCT"
        )
        
        # Save the index
        self.vector_db.save_local(self.db_path)

    def classify_query(self, query: str) -> str:
        query = query.lower()
        
        if "compare" in query or "source vs target" in query or "etl" in query:
            return "comparison"
        elif "clean" in query or "fix" in query or "correct" in query:
            return "cleaning"
        elif "null" in query or "missing" in query or "empty" in query:
            return "completeness"
        elif "accuracy" in query or "valid" in query or "correctness" in query:
            return "accuracy"
        else:
            return "completeness"  # default to completeness

    def select_llm(self, query: str) -> str:
        query = query.lower()
        if "code" in query or "sql" in query or "generate" in query:
            return "codellama:7b"
        elif len(query) > 300 or "explain" in query or "describe" in query:
            return "llama3"
        else:
            return "mistral"



    def save_to_file(self, answer: str, output_type: str, query_type: str):
        if output_type == "script":
            valid_formats = ["sql", "py", "java", "sh"]
            default_ext = "sql" if query_type in ["completeness", "accuracy"] else "py"
        else:  # report
            valid_formats = ["txt", "md", "html"]
            default_ext = "md"
        
        output_format = input(
            f"Choose {output_type} format ({'/'.join(valid_formats)}): "
        ).strip().lower()
        
        if output_format not in valid_formats:
            print(f"Invalid format. Defaulting to '{default_ext}'")
            output_format = default_ext
        
        name = input(f"Enter a name for the {output_type} file (without extension): ").strip()
        if not name:
            name = f"validation_{query_type}"
        
        output_file = f"results/{name}_{output_type}.{output_format}"
        
        # Extract code blocks if saving as script
        if output_type == "script":
            if f'```{output_format}' in answer:
                content = answer.split(f'```{output_format}')[1].split('```')[0].strip()
            else:
                content = answer.strip()
        else:
            content = answer
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"✅ Saved {output_type} to {output_file}")

    def load_vector_db(self):
        self.vector_db = FAISS.load_local(
            folder_path=self.db_path,
            embeddings=self.embedding,
            allow_dangerous_deserialization=True
        )

    def query_rag_system(self):
        if not self.vector_db:
            self.load_vector_db()
            
        retriever = self.vector_db.as_retriever()
        
        while True:
            query = input("\n🔍 Enter your question (or type 'exit'): ")
            if query.lower() in ["exit", "quit"]:
                break

            # Classify query and select appropriate LLMs
            query_type = self.classify_query(query)
            llm_model = self.select_llm(query)
            
            llm = OllamaLLM(
                model=f"{llm_model}",
                temperature=0.1,
                top_k=10,
                repeat_penalty=1.1
            )
            
            # Use appropriate prompt template
            if query_type == "comparison" and self.target_db_config:
                # For comparisons, get both contexts
                all_docs = self.vector_db.similarity_search(query, k=6)
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
                # For other query types, use standard retrieval
                qa = RetrievalQA.from_chain_type(
                    llm=llm,
                    retriever=retriever,
                    return_source_documents=True,
                    chain_type_kwargs={
                        "prompt": PROMPT_TEMPLATES[query_type]
                    }
                )
                result = qa(query)

            answer = result["result"]
            
            print("\n🧠 Answer:\n", answer)
            
            self.handle_output(answer, query_type)


    def handle_output(self, answer: str, query_type: str):
        print("\n💡 Output Options:")
        print("1. View in terminal")
        print("2. Save as script")
        print("3. Save as report")
        print("4. Save as both script and report")
        
        choice = input("Select output option (1-4): ").strip()
        
        if choice == "1":
            return
            
        if choice in ["2", "4"]:
            self.save_to_file(answer, "script", query_type)
            
        if choice in ["3", "4"]:
            self.save_to_file(answer, "report", query_type)
