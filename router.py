"""router.py — Semantic intent classifier for the Flipkart E-Commerce Chatbot.

Since `semantic-router` does not yet support Python 3.14, this module
implements equivalent functionality using `sentence_transformers` directly:

  1. Each route has a set of example utterances.
  2. At import time, all utterance embeddings are computed once.
  3. At query time, the user query is embedded and compared (cosine similarity)
     against every utterance. The route whose best-matching utterance exceeds
     the confidence threshold wins.
  4. If no route clears the threshold the query is marked "unknown".

This approach is functionally identical to semantic-router[local] and uses the
same underlying model (all-MiniLM-L6-v2).
"""

from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# Model (shared with ChromaDB — already downloaded)
# ---------------------------------------------------------------------------
_MODEL_NAME = "all-MiniLM-L6-v2"
_model = SentenceTransformer(_MODEL_NAME)

# Minimum cosine-similarity score for a route to be selected.
# Queries below this threshold for all routes fall through to "unknown".
_THRESHOLD = 0.45

# ---------------------------------------------------------------------------
# Route utterances
# ---------------------------------------------------------------------------

_ROUTES: dict[str, list[str]] = {
    "faq": [
        # Return / refund
        "What is the return policy of the products?",
        "How do I return a product?",
        "How long does it take to process a refund?",
        "What is the refund timeline?",
        "Can I get a refund on my order?",
        # Order tracking & cancellation
        "How can I track my order?",
        "Where is my order?",
        "Can I cancel my order?",
        "Can I modify my order after placing it?",
        # Payment & discounts
        "Do I get discount with the HDFC credit card?",
        "What payment methods are accepted?",
        "Are there any ongoing sales or promotions?",
        "How do I apply a promo code?",
        "Is online payment available?",
        # Shipping
        "Do you offer international shipping?",
        "How long does delivery take?",
        # Damaged / defective
        "What should I do if I receive a damaged product?",
        "I received a wrong item, what do I do?",
    ],
    "sql": [
        # Product search by brand
        "I want to buy Nike shoes that have 50% discount.",
        "Are there any Puma shoes on sale?",
        "What Adidas shoes are available?",
        "Show me Reebok running shoes.",
        "List all Skechers products.",
        # Price-based queries
        "Are there any shoes under Rs. 3000?",
        "Show women's shoes below 2000 rupees.",
        "Find me the cheapest running shoes.",
        "What are the most expensive shoes on Flipkart?",
        # Rating-based queries
        "Show me top rated sports shoes.",
        "List all shoes with rating above 4.5.",
        "Which shoes have the best reviews?",
        # Discount queries
        "Which shoes have the highest discount?",
        "Show products with more than 40% off.",
        # General product queries
        "Do you have formal shoes?",
        "What running shoes do you have?",
        "Show me casual sneakers.",
        "I am looking for sports shoes.",
        "Give me a list of available products.",
    ],
    "chitchat": [
        "Hello!",
        "Hi there",
        "Hey, how are you?",
        "Who are you?",
        "What can you do?",
        "What are you?",
        "Good morning",
        "Good evening",
        "Thanks",
        "Thank you",
        "You are helpful",
        "Help me",
        "What is the weather today?",
        "Tell me a joke",
        "I need help",
        "What should I buy?",
        "Suggest me something",
        "Bye",
        "Goodbye",
        "See you later",
    ],
}

# ---------------------------------------------------------------------------
# Pre-compute utterance embeddings at import time
# ---------------------------------------------------------------------------

def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two 1-D vectors."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))


print("[router] Encoding route utterances…")
_route_embeddings: dict[str, np.ndarray] = {}
for _route_name, _utterances in _ROUTES.items():
    _route_embeddings[_route_name] = _model.encode(
        _utterances, convert_to_numpy=True, normalize_embeddings=True
    )
print("[router] Done — semantic router ready.")


# ---------------------------------------------------------------------------
# Public classify function
# ---------------------------------------------------------------------------

def classify_query(query: str) -> str:
    """Classify the user's query into 'faq', 'sql', 'chitchat', or 'unknown'.

    Uses cosine similarity between the query embedding and pre-computed
    utterance embeddings for each route. The route with the highest
    similarity that also exceeds _THRESHOLD is returned.

    Returns:
        Route name as a string: 'faq' | 'sql' | 'chitchat' | 'unknown'
    """
    query_emb = _model.encode(
        query, convert_to_numpy=True, normalize_embeddings=True
    )

    best_route = "unknown"
    best_score = _THRESHOLD  # must beat threshold to win

    for route_name, utterance_embs in _route_embeddings.items():
        # Score = best (max) similarity across all utterances of this route
        scores = utterance_embs @ query_emb  # dot product; already normalized
        max_score = float(np.max(scores))
        if max_score > best_score:
            best_score = max_score
            best_route = route_name

    return best_route


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test_queries = [
        "What is your policy on defective product?",
        "Pink Puma shoes in price range 5000 to 10000",
        "Hello! Who are you?",
        "Tell me about quantum physics",
    ]
    for q in test_queries:
        print(f"Query : {q!r}")
        print(f"Route : {classify_query(q)}\n")
