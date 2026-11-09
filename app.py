import streamlit as st
from query import ask 

st.set_page_config(page_title="CineBrain", page_icon="🎬", layout="centered")

st.title("🎬 CineBrain")
st.caption("A RAG-powered film analyst that answers from Roger Ebert's reviews")
# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input
if question := st.chat_input("Ask me anything about films..."):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Get answer
    with st.chat_message("assistant"):
        with st.spinner("Searching reviews..."):
            result = ask(question)

        st.markdown(result["answer"])

        # Show sources
        with st.expander("📚 Sources"):
            for s in result["sources"]:
                stars = "⭐" * int(s["rating"]) if s["rating"] > 0 else "unrated"
                st.markdown(f"**{s['title']}** — {stars} ({s['rating']}/4.0)  \n[Read review]({s['url']})")

    st.session_state.messages.append({"role": "assistant", "content": result["answer"]})