"""app.py — Streamlit UI for the Flipkart E-Commerce GenAI Chatbot.

Features:
  • Flipkart-inspired blue/orange color theme
  • Sidebar with branding, how-it-works info, route badge, and clear chat
  • Chat bubbles with distinct user / assistant styling
  • Route badge displayed inline with each assistant response
  • Context-aware spinner messages
  • Welcome message on first load
"""

import streamlit as st
import router
import query_engine

# ---------------------------------------------------------------------------
# Page configuration — must be the first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Flipkart AI Assistant",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* ── Google Font ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ── Hide default Streamlit chrome ── */
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
    header    { visibility: hidden; }

    /* ── App background ── */
    .stApp {
        background: linear-gradient(135deg, #0a1628 0%, #0f2044 50%, #091830 100%);
        min-height: 100vh;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1f3c 0%, #0a1628 100%);
        border-right: 1px solid rgba(255,255,255,0.07);
    }
    section[data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }

    /* ── Main chat column ── */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1rem;
        max-width: 860px;
    }

    /* ── Page header ── */
    .page-header {
        background: linear-gradient(90deg, #2874f0 0%, #1a56c4 100%);
        border-radius: 16px;
        padding: 20px 28px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 16px;
        box-shadow: 0 4px 24px rgba(40,116,240,0.35);
    }
    .page-header h1 {
        color: #ffffff !important;
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.3px;
    }
    .page-header p {
        color: rgba(255,255,255,0.82) !important;
        font-size: 0.9rem;
        margin: 4px 0 0;
    }

    /* ── User chat bubble ── */
    .user-bubble {
        background: linear-gradient(135deg, #2874f0 0%, #1a56c4 100%);
        color: #ffffff;
        border-radius: 18px 18px 4px 18px;
        padding: 12px 18px;
        margin: 6px 0 6px 60px;
        box-shadow: 0 2px 12px rgba(40,116,240,0.3);
        font-size: 0.95rem;
        line-height: 1.5;
        animation: slideInRight 0.25s ease;
    }

    /* ── Assistant chat bubble ── */
    .assistant-bubble {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        color: #e2e8f0;
        border-radius: 18px 18px 18px 4px;
        padding: 14px 18px;
        margin: 6px 60px 6px 0;
        box-shadow: 0 2px 12px rgba(0,0,0,0.3);
        font-size: 0.95rem;
        line-height: 1.6;
        backdrop-filter: blur(8px);
        animation: slideInLeft 0.25s ease;
    }

    /* ── Route badge ── */
    .badge-faq {
        display: inline-block;
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(52, 211, 153, 0.3);
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
        text-transform: uppercase;
    }
    .badge-sql {
        display: inline-block;
        background: rgba(251, 146, 60, 0.15);
        color: #fb923c;
        border: 1px solid rgba(251, 146, 60, 0.3);
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
        text-transform: uppercase;
    }
    .badge-chitchat {
        display: inline-block;
        background: rgba(139, 92, 246, 0.15);
        color: #a78bfa;
        border: 1px solid rgba(167, 139, 250, 0.3);
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
        text-transform: uppercase;
    }
    .badge-unknown {
        display: inline-block;
        background: rgba(100, 116, 139, 0.15);
        color: #94a3b8;
        border: 1px solid rgba(148, 163, 184, 0.3);
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
        text-transform: uppercase;
    }

    /* ── Welcome card ── */
    .welcome-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.09);
        border-radius: 16px;
        padding: 24px;
        margin: 10px 0 20px;
        text-align: center;
        backdrop-filter: blur(6px);
    }
    .welcome-card h3 {
        color: #e2e8f0 !important;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .welcome-card p {
        color: #94a3b8 !important;
        font-size: 0.88rem;
        margin: 0;
        line-height: 1.6;
    }

    /* ── Suggested chips ── */
    .chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        justify-content: center;
        margin-top: 16px;
    }
    .chip {
        background: rgba(40,116,240,0.15);
        border: 1px solid rgba(40,116,240,0.3);
        color: #7eb3ff;
        border-radius: 20px;
        padding: 6px 14px;
        font-size: 0.82rem;
        cursor: pointer;
        transition: all 0.2s;
    }
    .chip:hover {
        background: rgba(40,116,240,0.3);
        color: #ffffff;
    }

    /* ── Sidebar divider ── */
    .sidebar-divider {
        border: none;
        border-top: 1px solid rgba(255,255,255,0.1);
        margin: 16px 0;
    }

    /* ── Sidebar section title ── */
    .sidebar-section {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        color: #64748b !important;
        margin-bottom: 10px;
    }

    /* ── How it works list ── */
    .how-item {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        margin-bottom: 12px;
    }
    .how-icon {
        font-size: 1.2rem;
        flex-shrink: 0;
        margin-top: 1px;
    }
    .how-text {
        font-size: 0.83rem;
        color: #94a3b8 !important;
        line-height: 1.5;
    }
    .how-text strong {
        color: #cbd5e1 !important;
    }

    /* ── Animations ── */
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(20px); }
        to   { opacity: 1; transform: translateX(0); }
    }
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-20px); }
        to   { opacity: 1; transform: translateX(0); }
    }

    /* ── Chat input ── */
    .stChatInput > div {
        border-radius: 12px !important;
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
    }
    .stChatInput textarea {
        color: #e2e8f0 !important;
        background: transparent !important;
    }

    /* ── Spinner ── */
    .stSpinner > div {
        border-color: #2874f0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center; padding: 12px 0 8px;">
            <div style="font-size: 2.8rem;">🛒</div>
            <div style="font-size: 1.25rem; font-weight: 700; color: #ffffff; margin-top: 6px;">
                Flipkart AI
            </div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 2px;">
                Shopping & Support Assistant
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

    # Last route badge
    st.markdown('<div class="sidebar-section">Last Query Route</div>', unsafe_allow_html=True)
    last_route = st.session_state.get("last_route", None)
    if last_route == "faq":
        st.markdown('<span class="badge-faq">📚 FAQ Retrieval</span>', unsafe_allow_html=True)
    elif last_route == "sql":
        st.markdown('<span class="badge-sql">🔍 Product Search</span>', unsafe_allow_html=True)
    elif last_route == "chitchat":
        st.markdown('<span class="badge-chitchat">💬 Chitchat</span>', unsafe_allow_html=True)
    elif last_route == "unknown":
        st.markdown('<span class="badge-unknown">❓ Unknown</span>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<span style="color:#4a5568; font-size:0.83rem;">No query yet</span>',
            unsafe_allow_html=True,
        )

    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

    # How it works
    st.markdown('<div class="sidebar-section">How It Works</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="how-item">
            <span class="how-icon">🧭</span>
            <span class="how-text"><strong>Semantic Router</strong> classifies your query into FAQ, Product Search, or Chitchat.</span>
        </div>
        <div class="how-item">
            <span class="how-icon">📚</span>
            <span class="how-text"><strong>FAQ queries</strong> are answered via ChromaDB vector search + Groq LLM summarization.</span>
        </div>
        <div class="how-item">
            <span class="how-icon">🔍</span>
            <span class="how-text"><strong>Product queries</strong> use Text-to-SQL (Groq) + pandasql to search the product catalog.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

    # Clear chat button
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_route = None
        st.rerun()

    st.markdown(
        '<div style="font-size:0.72rem; color:#334155; text-align:center; margin-top:16px;">'
        "Powered by Groq · ChromaDB · Sentence Transformers"
        "</div>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Main area — header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="page-header">
        <div style="font-size:2.4rem;">🛒</div>
        <div>
            <h1>Flipkart Support & Shopping Assistant</h1>
            <p>Ask me about our products, policies, orders, or anything shopping-related!</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_route" not in st.session_state:
    st.session_state.last_route = None

# ---------------------------------------------------------------------------
# Welcome card (shown only when no messages exist)
# ---------------------------------------------------------------------------
if not st.session_state.messages:
    st.markdown(
        """
        <div class="welcome-card">
            <h3>👋 Welcome! How can I help you today?</h3>
            <p>I can answer your questions about orders, returns, refunds, and<br>
            also help you search for products in our catalog.</p>
            <div class="chip-row">
                <span class="chip">📦 Return policy</span>
                <span class="chip">🔍 Nike shoes under ₹3000</span>
                <span class="chip">💳 HDFC card discount</span>
                <span class="chip">⭐ Top rated sports shoes</span>
                <span class="chip">🚚 Track my order</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Route badge helper
# ---------------------------------------------------------------------------
_BADGE_HTML = {
    "faq":      '<span class="badge-faq">📚 FAQ</span>',
    "sql":      '<span class="badge-sql">🔍 Product Search</span>',
    "chitchat": '<span class="badge-chitchat">💬 Chitchat</span>',
    "unknown":  '<span class="badge-unknown">❓ Unknown</span>',
}

_SPINNER_MESSAGES = {
    "faq":      "Searching our knowledge base…",
    "sql":      "Querying the product catalog…",
    "chitchat": "Thinking…",
    "unknown":  "Processing your request…",
}


def render_assistant_message(content: str, route: str) -> None:
    badge = _BADGE_HTML.get(route, "")
    st.markdown(
        f"""
        <div class="assistant-bubble">
            {badge}
            <div style="margin-top:{'6px' if badge else '0'};">{content}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_user_message(content: str) -> None:
    st.markdown(
        f'<div class="user-bubble">{content}</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Replay chat history
# ---------------------------------------------------------------------------
for message in st.session_state.messages:
    if message["role"] == "user":
        render_user_message(message["content"])
    else:
        render_assistant_message(message["content"], message.get("route", "unknown"))

# ---------------------------------------------------------------------------
# Handle new user input
# ---------------------------------------------------------------------------
if prompt := st.chat_input("Ask me anything about products or your orders…"):

    # Display & store user message
    render_user_message(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Classify intent
    route = router.classify_query(prompt)
    st.session_state.last_route = route

    # Generate response
    spinner_msg = _SPINNER_MESSAGES.get(route, "Thinking…")
    with st.spinner(spinner_msg):
        if route == "faq":
            response = query_engine.handle_faq(prompt)
        elif route == "sql":
            response = query_engine.handle_product_inquiry(prompt)
        elif route == "chitchat":
            response = (
                "Hey there! 👋 I'm Flipkart's AI Shopping & Support Assistant. "
                "I can help you search for products, check policies, track orders, "
                "and much more. What would you like to know?"
            )
        else:
            response = (
                "I'm not quite sure how to help with that. Could you rephrase your question? "
                "You can ask me about product searches, returns, payments, order tracking, or any shopping-related query."
            )

    # Display & store assistant response (with route tag for replay)
    render_assistant_message(response, route)
    st.session_state.messages.append(
        {"role": "assistant", "content": response, "route": route}
    )

    # Trigger a rerun so the sidebar route badge updates immediately
    st.rerun()
