"""data_ingestion.py — Ingest FAQ and e-commerce product data into their
respective stores (ChromaDB and SQLite).

This script is idempotent: it checks whether data already exists before
inserting, so it is safe to run multiple times without creating duplicates.
"""

import os
import sqlite3

import pandas as pd
import chromadb
from chromadb.utils import embedding_functions


# ---------------------------------------------------------------------------
# ChromaDB — FAQ ingestion
# ---------------------------------------------------------------------------

def ingest_faq_to_chroma(force: bool = False) -> None:
    """Ingest FAQ CSV data into ChromaDB.

    Args:
        force: If True, drop the existing collection and re-ingest from scratch.
    """
    print("Checking ChromaDB for existing FAQ data...")
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    if force:
        try:
            chroma_client.delete_collection("faq_collection")
            print("  Deleted existing 'faq_collection'.")
        except Exception:
            pass

    collection = chroma_client.get_or_create_collection(
        name="faq_collection",
        embedding_function=sentence_transformer_ef,
    )

    # Skip ingestion if data already exists
    existing_count = collection.count()
    if existing_count > 0 and not force:
        print(f"  FAQ collection already contains {existing_count} entries — skipping ingestion.")
        return

    faq_csv = "resources/faq_data.csv"
    if not os.path.exists(faq_csv):
        print(f"  Error: {faq_csv!r} not found. Skipping FAQ ingestion.")
        return

    faq_df = pd.read_csv(faq_csv)
    documents = faq_df["question"].tolist()
    metadatas = [{"answer": str(ans)} for ans in faq_df["answer"]]
    ids = [str(i) for i in range(len(faq_df))]

    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    print(f"  Successfully ingested {len(faq_df)} FAQs into ChromaDB.")


# ---------------------------------------------------------------------------
# SQLite — E-commerce product ingestion
# ---------------------------------------------------------------------------

def ingest_ecommerce_to_sqlite(force: bool = False) -> None:
    """Ingest e-commerce CSV data into the SQLite 'products' table.

    Args:
        force: If True, replace the existing table even if it already exists.
    """
    print("Checking SQLite for existing product data...")
    db_path = "ecommerce.db"

    if not force and os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='products';"
        )
        table_exists = cursor.fetchone() is not None
        if table_exists:
            cursor.execute("SELECT COUNT(*) FROM products;")
            row_count = cursor.fetchone()[0]
            conn.close()
            if row_count > 0:
                print(f"  'products' table already contains {row_count} rows — skipping ingestion.")
                return
        conn.close()

    ecommerce_csv = "resources/ecommerce_data_final.csv"
    if not os.path.exists(ecommerce_csv):
        print(f"  Error: {ecommerce_csv!r} not found. Skipping product ingestion.")
        return

    print("  Ingesting e-commerce product data into SQLite...")
    ecommerce_df = pd.read_csv(ecommerce_csv)
    conn = sqlite3.connect(db_path)
    ecommerce_df.to_sql("products", conn, if_exists="replace", index=False)
    conn.close()
    print(f"  Successfully ingested {len(ecommerce_df)} products into SQLite.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if not os.path.exists("resources"):
        print("Error: 'resources' directory not found. Please add your CSV files.")
        raise SystemExit(1)

    ingest_faq_to_chroma()
    ingest_ecommerce_to_sqlite()
    print("\nData ingestion complete.")
