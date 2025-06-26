# Enhanced chunking with semantic awareness and code-specific splitting

from langchain.text_splitter import (
    RecursiveCharacterTextSplitter, 
    PythonCodeTextSplitter,
    Language
)
from langchain_experimental.text_splitter import SemanticChunker
import re
import os

class EnhancedChunker:
    def __init__(self, embedding_model):
        self.embedding_model = embedding_model
        
    def get_code_splitter(self, language: str):
        language_map = {
            '.py': Language.PYTHON,
            '.js': Language.JS,
            '.java': Language.JAVA,
            '.cpp': Language.CPP,
            '.c': Language.C,
        }
        
        if language == '.sql':
            #a custom splitter for SQL
            return RecursiveCharacterTextSplitter(
                chunk_size=800,
                chunk_overlap=100,
                separators=[
                    "\n\n",  # Double newlines often separate SQL statements
                    "\n",    # Single newlines
                    ";",     # SQL statement terminators
                    " ",     # Spaces
                    ""       # Fallback
                ],
                length_function=len
            )
        elif language in language_map:
            return RecursiveCharacterTextSplitter.from_language(
                language=language_map[language],
                chunk_size=800,
                chunk_overlap=100,
                length_function=len
            )
        return None
    
    def smart_chunk_documents(self, documents):
        all_chunks = []
        
        for doc in documents:
            file_path = doc.metadata.get('source', '')
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext in ['.py', '.sql', '.js', '.java', '.cpp', '.c']:
                code_splitter = self.get_code_splitter(file_ext)
                if code_splitter:
                    chunks = code_splitter.split_documents([doc])
                else:
                    chunks = self.fallback_code_split([doc])
            
            elif file_ext in ['.md', '.txt', '.rst']:
                semantic_splitter = SemanticChunker(
                    embeddings=self.embedding_model,
                    breakpoint_threshold_type="percentile",
                    breakpoint_threshold_amount=95
                )
                chunks = semantic_splitter.split_documents([doc])
            
            # JSON/Config files - preserve structure
            elif file_ext in ['.json', '.yaml', '.yml', '.toml']:
                chunks = self.structure_aware_split([doc])
            
            else:
                chunks = self.fallback_code_split([doc])
            
            for chunk in chunks:
                chunk.metadata.update({
                    'file_type': file_ext,
                    'chunk_type': self.classify_chunk_content(chunk.page_content),
                    'language': self.detect_language(file_ext)
                })
            
            all_chunks.extend(chunks)
        
        return all_chunks
    
    def fallback_code_split(self, documents):
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=80,
            separators=[
                "\n\nclass ", "\n\ndef ", "\n\nfunction ",  # Function/class boundaries
                "\n\n", "\n", " ", ""  # Standard separators
            ],
            length_function=len
        )
        return splitter.split_documents(documents)
    
    def structure_aware_split(self, documents):
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=50,
            separators=["\n\n", "\n", ",", " ", ""],
            length_function=len
        )
        return splitter.split_documents(documents)
    
    def classify_chunk_content(self, content):
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ['def ', 'class ', 'function']):
            return 'function_definition'
        elif any(keyword in content_lower for keyword in ['import ', 'from ', 'include']):
            return 'imports'
        elif any(keyword in content_lower for keyword in ['select', 'insert', 'update', 'delete', 'create table']):
            return 'sql_query'
        elif content.strip().startswith('#') or content.strip().startswith('//'):
            return 'documentation'
        else:
            return 'general'
    
    def detect_language(self, file_ext):
        lang_map = {
            '.py': 'python',
            '.sql': 'sql',
            '.js': 'javascript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.md': 'markdown',
            '.json': 'json'
        }
        return lang_map.get(file_ext, 'unknown')