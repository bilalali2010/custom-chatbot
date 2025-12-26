import streamlit as st
import os
import requests
import PyPDF2
from dotenv import load_dotenv

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    st.error("⚠️ OPENROUTER_API_KEY not found. Set it in Streamlit Secrets or .env")
    st.stop()

# -----------------------------
# Page configuration
# -----------------------------
st.set_page_config(page_title="Custom AI Chatbot", layout="centered")
st.title("🤖 Custom Chatbot")

# -----------------------------
# File to store knowledge permanently
# -----------------------------
KNOWLEDGE_FILE = "knowledge.txt"
MAX_CONTEXT = 4500  # keep below model limits

# -----------------------------
# Admin PDF upload (only you)
# -----------------------------
admin_mode = st.checkbox("🔐 Admin Mode")

if admin_mode:
    st.subheader("Upload PDF for training (Admins only)")
    uploaded_file = st.file_uploader("Choose a PDF", type="pdf")

    if uploaded_file:
        reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""

        # Trim long text to safe length
        trimmed_text = text[:MAX_CONTEXT]

        with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
            f.write(trimmed_text)

        st.success("✅ PDF uploaded and knowledge saved.")
        st.write(f"Stored Characters: {len(trimmed_text)}")

# -----------------------------
# Load stored knowledge
# -----------------------------
if os.path.exists(KNOWLEDGE_FILE):
    with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
        knowledge = f.read()
else:
    knowledge = ""

# -----------------------------
# Chat interface for customers
# -----------------------------
st.subheader("Ask a question")
question = st.text_input("Type your question")

if question:
    if not knowledge:
        st.warning("⚠️ No knowledge available yet. Admin must upload PDF first.")
    else:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "nvidia/nemotron-3-nano-30b-a3b:free",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an AI assistant that answers questions ONLY based on the given document. "
                        "Keep answers short and accurate."
                    )
                },
                {
                    "role": "user",
                    "content": f"Document:\n{knowledge}\n\nQuestion:\n{question}"
                }
            ],
            "max_output_tokens": 180
        }

        with st.spinner("🤖 Thinking..."):
            try:
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                data = response.json()

                # If model sends an error
                if "error" in data:
                    st.error("❌ Model Error:")
                    st.json(data)
                else:
                    # Get actual answer
                    choices = data.get("choices", [])
                    if choices and "message" in choices[0]:
                        answer = choices[0]["message"]["content"]
                        st.markdown("### 🤖 Answer")
                        st.write(answer)
                    else:
                        st.error("⚠️ Empty response from model")
                        st.json(data)

            except Exception as err:
                st.error(f"Error calling the API: {err}")
