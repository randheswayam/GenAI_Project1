import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
import sqlite3
import os

def ingest_faq_to_chroma():
    print("Ingesting FAQ data into ChromaDB...")
    faq_df = pd.read_csv("resources/faq_data.csv")
    
    # Initialize ChromaDB persistent client
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    
    # Use sentence transformers embedding function
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    # Create or get collection
    collection = chroma_client.get_or_create_collection(
        name="faq_collection",
        embedding_function=sentence_transformer_ef
    )
    
    # Prepare data for insertion
    documents = faq_df['question'].tolist()
    metadatas = [{"answer": ans} for ans in faq_df['answer']]
    ids = [str(i) for i in range(len(faq_df))]
    
    # Add to collection
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    print(f"Successfully ingested {len(faq_df)} FAQs into ChromaDB.")

def ingest_ecommerce_to_sqlite():
    print("Ingesting E-commerce data into SQLite...")
    ecommerce_df = pd.read_csv("resources/ecommerce_data_final.csv")
    
    # Connect to SQLite
    conn = sqlite3.connect("ecommerce.db")
    
    # Save to SQLite table
    ecommerce_df.to_sql("products", conn, if_exists="replace", index=False)
    
    conn.close()
    print(f"Successfully ingested {len(ecommerce_df)} products into SQLite.")

if __name__ == "__main__":
    # Ensure resources directory exists
    if not os.path.exists("resources"):
        print("Error: resources directory not found.")
        exit(1)
        
    ingest_faq_to_chroma()
    ingest_ecommerce_to_sqlite()
    print("Data ingestion complete.")
