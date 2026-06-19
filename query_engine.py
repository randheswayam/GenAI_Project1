"""query_engine.py — Core query handlers for the Flipkart E-Commerce Chatbot.

Routing:
  • FAQ queries   → ChromaDB vector similarity search → Groq LLM summarization
  • SQL queries   → Groq Text-to-SQL → pandasql (sqldf) on a pandas DataFrame → Groq summarization
"""

import os
import sqlite3

import pandas as pd
from pandasql import sqldf
import chromadb
from chromadb.utils import embedding_functions
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Groq client setup
# ---------------------------------------------------------------------------
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL_NAME = "llama-3.3-70b-versatile"

# ---------------------------------------------------------------------------
# ChromaDB — FAQ vector store
# ---------------------------------------------------------------------------
chroma_client = chromadb.PersistentClient(path="./chroma_db")
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
faq_collection = chroma_client.get_or_create_collection(
    name="faq_collection",
    embedding_function=sentence_transformer_ef,
)

# ---------------------------------------------------------------------------
# Products DataFrame — loaded once at startup for use with pandasql
# ---------------------------------------------------------------------------
def _load_products_df() -> pd.DataFrame:
    """Load the products table from SQLite into a pandas DataFrame."""
    try:
        conn = sqlite3.connect("ecommerce.db")
        df = pd.read_sql_query("SELECT * FROM products", conn)
        conn.close()
        # Coerce numeric-looking columns so SQL comparisons work correctly
        for col in ["price", "avg_rating", "total_ratings", "discount"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    except Exception as e:
        print(f"[query_engine] Warning: could not load products DataFrame — {e}")
        return pd.DataFrame()


products = _load_products_df()

# ---------------------------------------------------------------------------
# Shared LLM helper
# ---------------------------------------------------------------------------

def get_llm_response(system_prompt: str, user_prompt: str) -> str:
    """Call the Groq LLM and return the assistant's reply."""
    completion = groq_client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
    )
    return completion.choices[0].message.content

# ---------------------------------------------------------------------------
# FAQ handler
# ---------------------------------------------------------------------------

def handle_faq(query: str) -> str:
    """Retrieve the top-3 FAQ results from ChromaDB and summarize with Groq."""
    results = faq_collection.query(query_texts=[query], n_results=3)

    if not results or not results.get("metadatas") or not results["metadatas"][0]:
        return "I'm sorry, I couldn't find an answer to your question in our FAQ."

    # Build context from retrieved Q&A pairs
    context_parts = []
    for i, (doc, meta) in enumerate(
        zip(results["documents"][0], results["metadatas"][0]), start=1
    ):
        context_parts.append(f"Q{i}: {doc}\nA{i}: {meta['answer']}")
    context = "\n\n".join(context_parts)

    system_prompt = (
        "You are a helpful customer support agent for Flipkart. "
        "Answer the user's question using ONLY the FAQ context provided below. "
        "Be concise, friendly, and accurate. If the context does not fully answer "
        "the question, say so politely.\n\n"
        f"FAQ Context:\n{context}"
    )
    return get_llm_response(system_prompt, query)

# ---------------------------------------------------------------------------
# Product / SQL handler
# ---------------------------------------------------------------------------

_SCHEMA_DESCRIPTION = """\
Table name : products
Columns:
  - product_link  (TEXT)   : URL of the product listing
  - title         (TEXT)   : product name / title
  - brand         (TEXT)   : brand name (e.g. Nike, Puma, Adidas, Reebok)
  - price         (REAL)   : price in Indian Rupees (numeric)
  - discount      (REAL)   : discount percentage (numeric, e.g. 40 means 40%)
  - avg_rating    (REAL)   : average customer rating out of 5 (numeric)
  - total_ratings (REAL)   : total number of customer ratings (numeric)

Important rules:
  - Use LOWER(column) for case-insensitive text comparisons.
  - Always add LIMIT 5 unless the user asks for a different number.
  - Return only valid SQL. Do not wrap in markdown code fences.
"""


def _clean_sql(raw: str) -> str:
    """Strip markdown fences that the LLM occasionally adds."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        # Remove first and last fence lines
        raw = "\n".join(
            line for line in lines if not line.strip().startswith("```")
        ).strip()
    return raw


def handle_product_inquiry(query: str) -> str:
    """Generate SQL with Groq, run it via pandasql, and summarize results."""
    global products

    if products.empty:
        return "I'm sorry, the product database is currently unavailable."

    # Step 1 — Generate SQL query
    system_sql = (
        "You are a SQL expert working with a pandas DataFrame called `products`. "
        "Write ONLY a valid SQL SELECT query to answer the user's question. "
        "Use the schema below. Return nothing but the SQL query.\n\n"
        + _SCHEMA_DESCRIPTION
    )
    raw_sql = get_llm_response(system_sql, query)
    sql_query = _clean_sql(raw_sql)

    try:
        # Step 2 — Execute via pandasql (operates on the in-memory DataFrame)
        # pandasql needs a local variable named 'products'
        result_df = sqldf(sql_query, {"products": products})

        if result_df is None or result_df.empty:
            return "I couldn't find any products matching your criteria. Try a different search!"

        # Cap at 5 rows to stay within LLM context limits
        result_df = result_df.head(5)

        # Step 3 — Summarize results with Groq
        result_text = result_df.to_string(index=False)
        system_summary = (
            "You are a helpful customer support agent for Flipkart. "
            "Summarize the product data below to answer the user's question clearly and concisely. "
            "Present prices in ₹, mention ratings and discounts where relevant. "
            "Format the response in a readable way using bullet points or a short list."
        )
        user_summary = (
            f"User Question: {query}\n\n"
            f"Product Data (up to 5 results):\n{result_text}"
        )
        return get_llm_response(system_summary, user_summary)

    except Exception as e:
        return (
            f"I encountered an error while searching for products. "
            f"Please try rephrasing your question.\n\n*(Debug: {e})*"
        )
