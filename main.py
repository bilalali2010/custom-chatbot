import streamlit as st
import os
import requests
import PyPDF2
from dotenv import load_dotenv

# Load local .env (optional, Streamlit Secrets will override)
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    st.error("⚠️ OPENROUTER_API_KEY not found. Set it in Streamlit Secrets.")
    st.stop()

st.set_page_config(page_title="Custom AI Chatbot", layout="centered")
st.title("🤖 Custom Chatbot")

# -----------------------------
# Admin PDF Upload (only you)
# -----------------------------
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

# Toggle for admin mode
admin_mode = st.checkbox("Admin Mode (Upload PDF)")

if admin_mode:
    uploaded_file = st.file_uploader("Upload PDF to train chatbot", type="pdf")
    if uploaded_file:
        reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        st.session_state.pdf_text = text
        st.success("PDF uploaded successfully!")

# -----------------------------
# Chat Interface for all users
# -----------------------------
st.subheader("Ask a question")

question = st.text_input("Type your question here:")

if question:
    if not st.session_state.pdf_text:
        st.warning("No PDF uploaded yet. Admin must upload PDF first.")
    else:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "allenai/olmo-3.1-32b-think:free",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Answer concisely in 2–3 sentences using only the uploaded PDF. "
                        "If the question is about personal introduction, answer in first person."
                    )
                },
                {
                    "role": "user",
                    "content": f"{st.session_state.pdf_text}\n\nQuestion: {question}"
                }
            ],
            "max_tokens": 100   # limits response length
        }

        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                data = response.json()
                answer = data["choices"][0]["message"]["content"]
                st.markdown("### 🤖 Answer")
                st.write(answer)
            except Exception as e:
                st.error(f"Error calling OpenRouter API: {e}")
