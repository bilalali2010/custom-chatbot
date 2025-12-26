import streamlit as st
import os
import requests
import PyPDF2
from dotenv import load_dotenv

# -----------------------------
# Load env
# -----------------------------
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    st.error("OPENROUTER_API_KEY missing")
    st.stop()

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="Custom AI Chatbot", layout="centered")
st.title("🤖 AI Assistant")

KNOWLEDGE_FILE = "knowledge.txt"

# -----------------------------
# ADMIN MODE (ONLY YOU)
# -----------------------------
admin_mode = st.checkbox("🔐 Admin Mode")

if admin_mode:
    st.subheader("Upload Training PDF (Admin Only)")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")

    if uploaded_file:
        reader = PyPDF2.PdfReader(uploaded_file)
        text = ""

        for page in reader.pages:
            text += page.extract_text() or ""

        with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
            f.write(text)

        st.success("✅ PDF saved permanently")

# -----------------------------
# LOAD KNOWLEDGE
# -----------------------------
if os.path.exists(KNOWLEDGE_FILE):
    with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
        knowledge = f.read()
else:
    knowledge = ""

# -----------------------------
# CHAT INTERFACE (CUSTOMERS)
# -----------------------------
st.subheader("Ask a question")

question = st.text_input("Type your question")

if question:
    if not knowledge:
        st.warning("Knowledge base not set. Admin must upload PDF.")
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
                        "Answer strictly using the provided knowledge. "
                        "Be concise (2–3 sentences). "
                        "If question is about introduction, answer in first person."
                    )
                },
                {
                    "role": "user",
                    "content": f"Knowledge:\n{knowledge}\n\nQuestion: {question}"
                }
            ],
            "max_tokens": 200
        }

        with st.spinner("Thinking..."):
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )

            data = response.json()

            answer = data.get("choices", [{}])[0].get("message", {}).get("content")

            if answer:
                st.markdown("### 🤖 Answer")
                st.write(answer)
            else:
                st.error("No answer returned")
