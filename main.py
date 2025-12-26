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

st.set_page_config(page_title="Custom AI Chatbot", layout="centered")
st.title("🤖 Custom AI Chatbot with Admin Control")

# -----------------------------
# File to store knowledge
# -----------------------------
KNOWLEDGE_DIR = "knowledge_pdfs"
if not os.path.exists(KNOWLEDGE_DIR):
    os.makedirs(KNOWLEDGE_DIR)

MAX_CONTEXT = 4500  # safe limit for model input
ADMIN_PASSWORD = "20100905"  # your password

# -----------------------------
# Initialize session state
# -----------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# -----------------------------
# Admin login
# -----------------------------
admin_mode = st.checkbox("🔐 Admin Mode (Login Required)")

if admin_mode:
    password_input = st.text_input("Enter Admin Password", type="password")
    if password_input != ADMIN_PASSWORD:
        st.warning("❌ Incorrect password!")
        st.stop()
    else:
        st.success("✅ Logged in as Admin")
        st.subheader("Upload PDF(s) for training")
        uploaded_files = st.file_uploader("Select PDF(s)", type="pdf", accept_multiple_files=True)
        if uploaded_files:
            combined_text = ""
            for uploaded_file in uploaded_files:
                reader = PyPDF2.PdfReader(uploaded_file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                combined_text += text + "\n\n"

                # Save PDF to knowledge directory
                with open(os.path.join(KNOWLEDGE_DIR, uploaded_file.name), "wb") as f:
                    f.write(uploaded_file.getbuffer())

            # Trim to safe length
            combined_text = combined_text[:MAX_CONTEXT]

            # Save combined text as knowledge.txt
            with open("knowledge.txt", "w", encoding
