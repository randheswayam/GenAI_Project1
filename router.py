import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL_NAME = "llama-3.3-70b-versatile"

def classify_query(query: str) -> str:
    """Classify the user's query into 'faq', 'product_inquiry', or 'unknown' using LLM."""
    system_prompt = """You are a router for an e-commerce customer support bot.
You must classify the user's query into exactly one of these two categories:
1. 'faq' - If the user is asking about return policies, tracking orders, payment methods, refunds, sales, promotions, cancellations, international shipping, damaged products, or promo codes.
2. 'product_inquiry' - If the user is asking to find products, shoes, prices, ratings, or searching for specific items to buy.

Respond ONLY with the exact string 'faq' or 'product_inquiry'. If completely unsure, respond with 'unknown'. Do not provide any other text."""
    
    try:
        completion = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0.0,
        )
        return completion.choices[0].message.content.strip().lower()
    except Exception as e:
        print(f"Router error: {e}")
        return "unknown"
