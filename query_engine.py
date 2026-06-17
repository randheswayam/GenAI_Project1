import os
import sqlite3
import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Initialize Groq client
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL_NAME = "llama-3.3-70b-versatile"

# Initialize ChromaDB persistent client and collection
chroma_client = chromadb.PersistentClient(path="./chroma_db")
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
faq_collection = chroma_client.get_or_create_collection(
    name="faq_collection",
    embedding_function=sentence_transformer_ef
)

def get_llm_response(system_prompt: str, user_prompt: str) -> str:
    completion = groq_client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0,
    )
    return completion.choices[0].message.content

def handle_faq(query: str) -> str:
    """Retrieve answer for FAQ query from ChromaDB."""
    results = faq_collection.query(
        query_texts=[query],
        n_results=1
    )
    if results and results['metadatas'] and len(results['metadatas'][0]) > 0:
        return results['metadatas'][0][0]['answer']
    return "I'm sorry, I couldn't find an answer to your question in our FAQ."

def handle_product_inquiry(query: str) -> str:
    """Use Text-to-SQL to answer product inquiries."""
    # Step 1: Generate SQL query
    schema = """
    Table name: products
    Columns: product_link (TEXT), title (TEXT), brand (TEXT), price (TEXT), discount (TEXT), avg_rating (TEXT), total_ratings (TEXT)
    Note: price, avg_rating, and total_ratings might be strings but contain numbers.
    """
    system_sql = f"You are a SQL expert. Given the following schema for an SQLite database, write ONLY a valid SQL query to answer the user's question. Return nothing but the SQL query. Do not wrap in markdown block.\n{schema}"
    
    sql_query = get_llm_response(system_sql, query).strip()
    
    # Clean markdown if accidentally included
    if sql_query.startswith("```sql"):
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
    elif sql_query.startswith("```"):
        sql_query = sql_query.replace("```", "").strip()
        
    try:
        # Step 2: Execute SQL query
        conn = sqlite3.connect("ecommerce.db")
        result_df = pd.read_sql_query(sql_query, conn)
        conn.close()
        
        # Step 3: Summarize results
        if result_df.empty:
            return "I couldn't find any products matching your criteria."
        
        # Convert result to a text representation
        result_text = result_df.to_string(index=False)
        system_summary = "You are a helpful customer support agent for Flipkart. Summarize the following data to answer the user's question clearly and concisely. Format it nicely."
        user_summary = f"User Question: {query}\n\nData Result:\n{result_text}"
        
        return get_llm_response(system_summary, user_summary)
        
    except Exception as e:
        return f"I encountered an error trying to find those products: {str(e)}"
