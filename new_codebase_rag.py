import os
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader
from langchain.chains import RetrievalQA
from langchain.chains import LLMChain
from langchain_community.document_loaders import TextLoader
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_ollama.llms import OllamaLLM
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from multiprocessing import Pool
from langchain_community.document_loaders import (TextLoader, PythonLoader, 
                                                        JSONLoader, BSHTMLLoader)
import time
from chunking import EnhancedChunker
from connect_alchemy import MySQLConnection
from typing import Dict, List, Optional
import pandas as pd
from new_prompt import NEW_PROMPT, VALIDATION_PROMPT
from execute_output import ExecuteOutput
import sqlparse

class CodebaseRAG:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.embed_model = "nomic-embed-text"  # or mxbai-embed-large for code
        self.embedding = OllamaEmbeddings(model=self.embed_model)
        self.chunker = EnhancedChunker(self.embedding)
        self.vector_db = None
        self.source_db_config = None
        self.target_db_config = None
        self.transformation_path = None

    def configure_databases(self, source_config: Dict, target_config: Optional[Dict] = None):
        self.source_db_config = source_config
        self.target_db_config = target_config
    
    def extract_transformation_logic(self, path: str) -> str:
        self.transformation_path = path
        with open(path, 'r') as file:
            results = file.read()

        statements = sqlparse.split(results)

        return statements
             

    def extract_database_into(self, database: Dict):
        return database

    def extract_schema_info(self, connection_config: Dict) -> List[Dict]:
        conn = MySQLConnection(**connection_config)
        schema_info = []
        
        try:
            # Get tables
            tables_df = conn.execute_query("SHOW TABLES")
            print("Tables found:", tables_df)
            
            for idx, row in tables_df.iterrows():
                table_name = row.iloc[0]  # Get first column value
                
                # Get columns
                columns_df = conn.execute_query(f"""
                        SELECT 
                            COLUMN_NAME,
                            DATA_TYPE,
                            IS_NULLABLE,
                            COLUMN_DEFAULT,
                            COLUMN_KEY,
                            EXTRA,
                            CHARACTER_MAXIMUM_LENGTH,
                            NUMERIC_PRECISION,
                            NUMERIC_SCALE
                        FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_SCHEMA = '{connection_config['database']}' 
                        AND TABLE_NAME = '{table_name}'
                        ORDER BY ORDINAL_POSITION
                    """)
                columns = columns_df.to_dict('records')  # Convert to list of dicts
                
                # Get foreign keys
                fks_df = conn.execute_query(f"""
                    SELECT 
                        COLUMN_NAME, 
                        REFERENCED_TABLE_NAME, 
                        REFERENCED_COLUMN_NAME
                    FROM 
                        INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                    WHERE 
                        TABLE_NAME = '{table_name}' 
                        AND REFERENCED_TABLE_NAME IS NOT NULL
                """)
                fks = fks_df.to_dict('records') if not fks_df.empty else []
                
                schema_info.append({
                    'table_name': table_name,
                    'columns': columns,
                    'foreign_keys': fks
                })
        finally:
            conn.close()
                
        return schema_info

    def profile_data(self, connection_config: Dict) -> List[Dict]:
        conn = MySQLConnection(**connection_config)
        profile_info = []
        
        try:
            tables_df = conn.execute_query("SHOW TABLES")
            
            for idx, row in tables_df.iterrows():
                table_name = row.iloc[0]  # Get first column value
                
                # Basic stats
                count_df = conn.execute_query(f"SELECT COUNT(*) as row_count FROM {table_name}")
                row_count = count_df.iloc[0]['row_count']
                
                # Column profiles
                columns_df = conn.execute_query(f"DESCRIBE {table_name}")
                column_profiles = []
                
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
                    
                    null_count = stats_df.iloc[0]['null_count']
                    distinct_count = stats_df.iloc[0]['distinct_count']
                    
                    sample_df = conn.execute_query(f"""
                        SELECT `{col_name}` 
                        FROM {table_name} 
                        WHERE `{col_name}` IS NOT NULL
                        LIMIT 5
                    """)
                    
                    sample_values = sample_df[col_name].tolist() if not sample_df.empty else []
                    
                    column_profiles.append({
                        'name': col_name,
                        'type': col_type,
                        'null_count': null_count,
                        'distinct_count': distinct_count,
                        'sample_values': sample_values
                    })
                
                profile_info.append({
                    'table_name': table_name,
                    'row_count': row_count,
                    'columns': column_profiles
                })
        finally:
            conn.close()
                
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
        database_info = self.extract_database_into(self.source_db_config)
        documents.append(Document(
                    page_content="Source Database Information:\n" + str(database_info),
                    metadata={
                        'source': 'source_db'
                    }
        ))

        database_info = self.extract_database_into(self.target_db_config)
        documents.append(Document(
                    page_content="Target Database Information:\n" + str(database_info),
                    metadata={
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

    #NOT USING FOR NOW - JUST TESTING ONLY ONE NEW PROMPT
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

    def select_llm_optimized(self, query: str) -> tuple:
        query_lower = query.lower()
        
        # # Simple SQL operations - Use CodeLlama (fastest)
        # if any(word in query_lower for word in ["select", "count", "null", "missing", "empty"]):
        #     return ("codellama:7b", {
        #         "temperature": 0.0,
        #         "top_k": 1,
        #         "top_p": 0.1,
        #         "num_predict": 256,
        #         "stop": ["```", ";", "\n\n"],
        #         "num_ctx": 2048,
        #         "num_batch": 16
        #     })
        
        # # Complex transformations/ETL - Use DeepSeek R1 (best reasoning)
        # elif any(word in query_lower for word in ["transform", "etl", "complex", "join", "migration", "compare"]):
        #     return ("deepseek-r1:8b", {
        #         "temperature": 0.1,
        #         "top_k": 5,
        #         "top_p": 0.8,
        #         "repeat_penalty": 1.05,
        #         "num_predict": 1024,
        #         "stop": ["```", "\n\n\n"],
        #         "num_ctx": 4096,
        #         "num_batch": 8
        #     })
        
        # # Validation scripts - Use DeepSeek R1 with focused parameters
        # elif any(word in query_lower for word in ["validate", "check", "verify", "test"]):
        #     return ("deepseek-r1:8b", {
        #         "temperature": 0.05,
        #         "top_k": 3,
        #         "top_p": 0.7,
        #         "repeat_penalty": 1.02,
        #         "num_predict": 512,
        #         "stop": ["```", ";", "\n\n"],
        #         "num_ctx": 3072
        #     })
        
        # # Analysis and explanations - Use Mistral
        # elif any(word in query_lower for word in ["explain", "analyze", "describe", "report", "why", "how"]):
        #     return ("mistral:7b", {
        #         "temperature": 0.2,
        #         "top_k": 10,
        #         "top_p": 0.9,
        #         "repeat_penalty": 1.1,
        #         "num_predict": 800,
        #         "stop": ["```", "\n\n\n"],
        #         "num_ctx": 3072,
        #         "mirostat": 2,
        #         "mirostat_tau": 5.0,
        #         "mirostat_eta": 0.1
        #     })
        
        # # Default: Fast CodeLlama for general queries
        # else:
        return ("codellama:7b", {
                "temperature": 0.1,  # Slightly higher for variety
                "top_k": 5,          # Allow more token choices
                "num_predict": 1024, # Increase token limit significantly
                "num_ctx": 2048
            })
    def select_llm(self, query: str) -> str:
        query = query.lower()
        if "code" in query or "sql" in query or "generate" in query:
            return "codellama:7b"
        elif len(query) > 300 or "explain" in query or "describe" in query:
            return "llama3"




    def save_to_file(self,answer: str, output_type: str):
        if output_type == "script":
            output_format = "sql" 
        else:  # report
            output_format = "txt"
        
        name = input(f"Enter a name for the {output_type} file (without extension): ").strip()
        if not name:
            name = f"validation"
        
        output_file = f"results/{name}_{output_type}.{output_format}"
        
        # Extract code blocks if saving as script
        if output_type == "script":
            # Find all SQL code blocks
            sql_blocks = []
            current_pos = 0
            while True:
                start_marker = f'```{output_format}'
                start_pos = answer.find(start_marker, current_pos)
                if start_pos == -1:
                    break
                end_pos = answer.find('```', start_pos + len(start_marker))
                if end_pos == -1:
                    break
                sql_block = answer[start_pos + len(start_marker):end_pos].strip()
                sql_blocks.append(sql_block)
                current_pos = end_pos + 3
            
            if sql_blocks:
                content = "\n\n".join(sql_blocks)
            else:
                content = answer.strip()
        else:
            content = answer
        
        # Create results directory if it doesn't exist
        import os
        os.makedirs("results", exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"✅ Saved {output_type} to {output_file}")
        if output_type == "script":
            return output_file
        

    def load_vector_db(self):
        self.vector_db = FAISS.load_local(
            folder_path=self.db_path,
            embeddings=self.embedding,
            allow_dangerous_deserialization=True
        )

    def query_rag_system(self):
        if not self.vector_db:
            self.load_vector_db()
            
        retriever = self.vector_db.as_retriever(
            search_kwargs={
                "k": 3,  # Reduce from 6 to 3 most relevant chunks
                "fetch_k": 6,  # Reduce initial fetch
                "score_threshold": 0.7  # Only high-relevance chunks
            }
        )
        
        while True:
            query = input("\n🔍 Enter your question (or type 'exit'): ")
            if query.lower() in ["exit", "quit"]:
                break

            # Classify query and select appropriate LLMs
            # query_type = self.classify_query(query)
            model_name, params = self.select_llm_optimized(query)
            print(model_name)
            
            llm = OllamaLLM(
                model=f"{model_name}",
                **params
            )
            
            # Use appropriate prompt template
            # if query_type == "comparison" and self.target_db_config:
            #     # For comparisons, get both contexts
            #     all_docs = self.vector_db.similarity_search(query, k=6)
            #     source_docs = [doc for doc in all_docs if doc.metadata.get("source") == "source_db"]
            #     target_docs = [doc for doc in all_docs if doc.metadata.get("source") == "target_db"]
                
            #     source_context = "\n".join([doc.page_content for doc in source_docs[:3]])
            #     target_context = "\n".join([doc.page_content for doc in target_docs[:3]])
                
            #     prompt = PROMPT_TEMPLATES[query_type].format(
            #         source_context=source_context,
            #         target_context=target_context,
            #         question=query
            #     )
                
            #     result = {"result": llm.invoke(prompt)}
            # For other query types, use standard retrieval

            # Load transformation logic once
            if hasattr(self, 'transformation_logic_path'):
                transformation_logic = self.extract_transformation_logic(self.transformation_logic_path)
                # Convert list to string if it's a list
                if isinstance(transformation_logic, list):
                    transformation_logic = "\n".join(transformation_logic)
            else:
                transformation_logic = "No transformation logic provided"

            retrieved_docs = retriever.invoke(query)
            context = "\n".join(doc.page_content for doc in retrieved_docs)


            # qa = RetrievalQA.from_chain_type(
            #         llm=llm,
            #         retriever=retriever,
            #         return_source_documents=True,
            #         chain_type_kwargs={
            #             "prompt": NEW_PROMPT
            #         }
            #     )

            llm_chain = LLMChain(
                    llm=llm,
                    prompt=VALIDATION_PROMPT
                )


            start_time = time.time()
            # result = qa.invoke({
            #         "context": context,
            #         "transformation_logic": transformation_logic,
            #         "query": query
            #     })
            result = llm_chain.invoke({
                "context": context,
                "source_db": self.source_db_config.get('database', 'source_db'),
                "target_db": self.target_db_config.get('database', 'target_db'),
                "transformation_logic": transformation_logic,
                "query": query  # or "question" — depending on your NEW_PROMPT definition
            })
            end_time = time.time()
            print(f"⏱️ Query processed in {end_time - start_time:.2f} seconds")
            # print(result)
            answer = result["text"]


            
            print("\n🧠 Answer:\n", answer)
            
            file_name = self.handle_output(answer)
            executor = ExecuteOutput(script_filename=file_name)
            # Execute the final script
            executor.execute_final(self.source_db_config)



    def handle_output(self, answer: str):
        print("\n💡 Output Options:")
        print("1. View in terminal")
        print("2. Save as script")
        print("3. Save as script and report")
        
        choice = input("Select output option (1/2/3): ").strip()
        
        if choice == "1":
            return
            
        if choice in ["2","3"]:
            script_name = self.save_to_file(answer, "script")
        if choice == "3":
            self.save_to_file(answer, "report")

        return script_name
