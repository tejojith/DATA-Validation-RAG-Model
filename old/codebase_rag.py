import os
from langchain_community.vectorstores import FAISS
#from langchain_community.embeddings import OllamaEmbeddings
#from langchain_community.llms import Ollama
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader
from langchain.chains import RetrievalQA
from langchain_community.document_loaders import TextLoader
#from :class:`~langchain_ollama import OllamaLLM`
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

from conn_sql import MySQLConnection


VALIDATION_PROMPT = PromptTemplate.from_template("""
You are a Data Validation Expert. Your task is to validate the data in the database.
you need to generate a test script according to the users query,
if not major is mentioned then you need to generate a test script that looks for null values, checks if the table has the same number of rows as it started with and other data validation tests.                                                
{context}
                                                 
User Query: {question}
                                                 
give output:
""")

#Output Mode: {mode}


class CodebaseRAG:
    def __init__(self, project_path, db_path):
        self.project_path = project_path
        self.db_path = db_path
        self.embed_model = "nomic-embed-text"  # or mxbai-embed-large for code
        
        self.embedding = OllamaEmbeddings(model=self.embed_model)
         # imported all the chunking functions
        self.chunker = EnhancedChunker(self.embedding)
        self.vector_db = None

    def save_to_file(self, answer):
        output_format = input("Choose a format to save results (e.g. sql, py): ").strip().lower()
        valid_formats = ["txt", "sql", "py", "java"]
        if output_format not in valid_formats:
            print(f"Invalid format. Defaulting to 'txt'")
            output_format = "txt"


        name = input("Enter a name for the output file (without extension): ").strip()
        if not name:
            output_file = f"rag_output.{output_format}"
        else:
            output_file = f"{name}_rag_output.{output_format}"

        with open(output_file, "w", encoding="utf-8") as f:
            if output_format == "txt":
                f.write(f"{answer}\n{'-'*40}\n")
            elif output_format == "sql":
                if '```sql' in answer:
                    sql_code = answer.split('```sql')[1].split('```')[0].strip()
                else:
                    sql_code = answer.strip()
                
                
                f.write(sql_code)
                print(f"{name}_rag_output.{output_format}")
                
            elif output_format == "py":
                if '```python' in answer:
                    code = answer.split('```python')[1].split('```')[0].strip()
                else:
                    code = answer.strip()
                f.write(code)
            elif output_format == "java":
                if '```java' in answer:
                    code = answer.split('```java')[1].split('```')[0].strip()
                else:
                    code = answer.strip()
                f.write(code)
        


    def create_embeddings_and_store(self):
        #loading the sql data

        mysql_config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'password',
            'database': 'sys'
        }
        
        # Initialize RAG system
        rag = MySQLConnection(**mysql_config)
        
        # Sample SQL query - modify based on your database schema
        # This example assumes a table with articles/documents
        sql_query = """
        SELECT 
            id,
            title,
            content,
            author,
            category,
            created_date
        FROM articles 
        WHERE content IS NOT NULL
        LIMIT 1000
        """
        
        # Step 1: Extract data from MySQL
        df = rag.extract_data_from_mysql(sql_query)
        
        if df is None or df.empty:
            print("❌ No data extracted. Check your database connection and query.")
            return
    
        print("🔄 Preparing documents...")
        documents = rag.prepare_documents(
            df=df,
            content_column='content',  # Main content column
            metadata_columns=['id', 'title', 'author', 'category', 'created_date']
        )


        #updated splitting and chunking

        chunks = self.chunker.smart_chunk_documents(documents)
        
        # Create FAISS index with optimized parameters
        self.vector_db = FAISS.from_documents(
            documents=chunks,
            embedding=self.embedding,
            distance_strategy="METRIC_INNER_PRODUCT"  # Faster than L2 for many cases
        )
        
        # Save the index
        self.vector_db.save_local(self.db_path)



    def load_vector_db(self):
        self.vector_db = FAISS.load_local(
            folder_path=self.db_path,
            embeddings=self.embedding,
            allow_dangerous_deserialization=True  # Only if you trust the source
        )
    def select_llm_for_query(query: str):
        if "code" in query.lower() or "sql" in query.lower() or "generate" in query.lower():
            return "codellama"
        elif len(query) > 300 or "explain" in query.lower():
            return "llama3"
        else:
            return "mistral"    

    def query_rag_system(self):
        if not self.vector_db:
            self.load_vector_db()
        retriever = self.vector_db.as_retriever()
        llm = OllamaLLM(model="codellama:7b",
                        temperature=0.1,  # Less randomness
                        top_k=10,  # Faster sampling
                        repeat_penalty=1.1  # Prevent repetition
                        )  # Use any: mistral, wizardcoder, codellama
        qa = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=True,chain_type_kwargs={"prompt": VALIDATION_PROMPT} )





        while True:
            query = input("\n🔍 Enter your question (or type 'exit'): ")
            if query.lower() in ["exit", "quit"]:
                break

            start_time = time.time()
            
            result = qa(query)
            answer = result["result"]
            print("\n🧠 Answer:\n", answer)
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"Time taken: {elapsed_time:.4f} seconds")

            ch = input("Do you want to save the result to file? (0 for yes, 1 for terminal): ").strip().lower()

            if ch == '0':
                self.save_to_file(answer)
            else:
                pass
