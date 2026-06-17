import streamlit as st
import router
import query_engine

st.set_page_config(page_title="Flipkart E-commerce Chatbot", page_icon="🛒")

st.title("🛒 Flipkart Support & Shopping Assistant")
st.write("Welcome! I can help you with your FAQs and product inquiries.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What are you looking for today?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Classify Query
    route = router.classify_query(prompt)
    
    # Process Query
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            if route == "faq":
                response = query_engine.handle_faq(prompt)
            elif route == "product_inquiry":
                response = query_engine.handle_product_inquiry(prompt)
            else:
                response = "I'm sorry, I'm not sure how to help with that. Could you please rephrase your question?"
                
            st.markdown(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
