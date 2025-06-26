from langchain.prompts import PromptTemplate

PROMPT_TEMPLATES = {
    "completeness": PromptTemplate.from_template("""
    You are a Data Completeness Validation Expert. Generate tests to check for:
    - NULL values in critical columns
    - Missing required fields
    - Empty strings where data should exist
    - Default values that might indicate missing data
    - give the output in python to be execute in MySQL
    
    Database Context: {context}
    
    User Query: {question}
    
    Generate a comprehensive completeness validation script:
    """),
    
    "accuracy": PromptTemplate.from_template("""
    You are a Data Accuracy Validation Expert. Generate tests to check:
    - Data type conformity
    - Value ranges
    - Referential integrity
    
    Database Context: {context}
    
    User Query: {question}
    
    Generate a comprehensive accuracy validation script:
    """),
    
    "comparison": PromptTemplate.from_template("""
    You are a Cross-Database Comparison Expert. Generate tests to:
    - Compare record counts between source and target
    - Validate data transformations
    - Verify ETL completeness
    - Identify data drift
    
    Source Database: {source_context}
    Target Database: {target_context}
    
    User Query: {question}
    
    Generate a comprehensive comparison validation script:
    """),
    
    "cleaning": PromptTemplate.from_template("""
    You are a Data Cleaning Expert. Generate scripts to:
    - Handle NULL values appropriately
    - Standardize formats
    - Correct data errors
    - Deduplicate records
    
    Database Context: {context}
    
    User Query: {question}
    
    Generate a comprehensive data cleaning script:
    """)
}