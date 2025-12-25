import streamlit as st
import os
import requests
import PyPDF2
from dotenv import load_dotenv
import pickle

# -----------------------------
# Load environment
# -----------------------------
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    st.error("⚠️ OPENROUTER_API_KEY not found. Set it in Streamlit Secrets or .env.")
    st.stop()

# -----------------------------
# App config
# -----------------------------
st.set_page_config(page_title="Custom AI Chatbot", layout="centered")
st.title("🤖 Custom Chatbot")

DATA_FILE = "pdf_text.pkl"  # Persistent storage

# -----------------------------
# Load existing PDF text
# -----------------------------
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "rb") as f:
        pdf_text = pickle.load(f)
else:
    pdf_text = ""

# -----------------------------
# Admin Login (Password Protected)
# -----------------------------
st.sidebar.title("Admin Login")
password_input = st.sidebar.text_input("Enter admin password", type="password")

ADMIN_PASSWORD = "mysecret123"  # Change this to your secure password
is_admin = password_input == ADMIN_PASSWORD

# -----------------------------
# Admin PDF Upload
# -----------------------------
if is_admin:
    st.sidebar.subheader("Admin Mode - Upload PDF")
    uploaded_file = st.sidebar.file_uploader("Upload PDF to train chatbot", type="pdf")
    if uploaded_file:
        reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        pdf_text = text
        # Save persistently
        with open(DATA_FILE, "wb") as f:
            pickle.dump(pdf_text, f)
        st.sidebar.success("PDF uploaded and saved successfully!")
elif password_input:
    st.sidebar.warning("❌ Incorrect password")

# -----------------------------
# Chat Interface for all users
# -----------------------------
st.subheader("Ask a question")

question = st.text_input("Type your question here:")

if question:
    if not pdf_text:
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
                    "content": f"{pdf_text}\n\nQuestion: {question}"
                }
            ],
            "max_tokens": 100
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
