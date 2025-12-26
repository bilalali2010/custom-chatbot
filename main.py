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

st.set_page_config(page_title="Custom AI Chatbot", layout="wide")
st.title("🤖ASK ANYTHING ABOUT BILAL")

# -----------------------------
# File to store knowledge
# -----------------------------
KNOWLEDGE_DIR = "knowledge_pdfs"
if not os.path.exists(KNOWLEDGE_DIR):
    os.makedirs(KNOWLEDGE_DIR)

MAX_CONTEXT = 4500  # safe limit for model input
ADMIN_PASSWORD = "20100905"  # admin password

# -----------------------------
# Initialize session state
# -----------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# -----------------------------
# Admin sidebar
# -----------------------------
with st.sidebar:
    st.header("🔐 Admin Panel")
    admin_mode = st.checkbox("Enable Admin Mode")

    if admin_mode:
        password_input = st.text_input("Enter Admin Password", type="password")
        if password_input != ADMIN_PASSWORD:
            st.warning("❌ Incorrect password!")
            st.stop()
        else:
            st.success("✅ Logged in as Admin")
            st.subheader("Upload PDF(s) for training")
            uploaded_files = st.file_uploader(
                "Select PDF(s)", type="pdf", accept_multiple_files=True
            )
            if uploaded_files:
                combined_text = ""
                for uploaded_file in uploaded_files:
                    reader = PyPDF2.PdfReader(uploaded_file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() or ""
                    combined_text += text + "\n\n"

                    # Save uploaded PDF to knowledge folder
                    with open(os.path.join(KNOWLEDGE_DIR, uploaded_file.name), "wb") as f:
                        f.write(uploaded_file.getbuffer())

                # Trim combined text to safe length
                combined_text = combined_text[:MAX_CONTEXT]

                # Save combined text as knowledge.txt
                with open("knowledge.txt", "w", encoding="utf-8") as f:
                    f.write(combined_text)

                st.success(f"✅ Knowledge stored successfully. Characters stored: {len(combined_text)}")

# -----------------------------
# Load knowledge for users
# -----------------------------
knowledge = ""
if os.path.exists("knowledge.txt"):
    with open("knowledge.txt", "r", encoding="utf-8") as f:
        knowledge = f.read()

# -----------------------------
# Chat interface
# -----------------------------
st.subheader("Ask a question")

col1, col2 = st.columns([4, 1])
with col1:
    question = st.text_input("Type your question here")

with col2:
    send = st.button("Send")

if send and question:
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
                        "You are an AI assistant that answers questions ONLY based on the provided document. "
                        "Keep answers short and accurate. If answer not in document, respond: 'Information not available.'"
                    )
                },
                {
                    "role": "user",
                    "content": f"Document:\n{knowledge}\n\nQuestion:\n{question}"
                }
            ],
            "max_output_tokens": 200,
            "temperature": 0.2
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

                if "error" in data:
                    st.error("❌ Model Error:")
                    st.json(data)
                else:
                    choices = data.get("choices", [])
                    if choices and "message" in choices[0]:
                        answer = choices[0]["message"].get("content")
                        st.session_state.chat_history.append((question, answer))
                        st.markdown("### 🤖 Answer")
                        st.write(answer)
                    else:
                        st.error("⚠️ Empty response from model")
                        st.json(data)
            except Exception as err:
                st.error(f"Error calling the API: {err}")

# -----------------------------
# Display chat history
# -----------------------------
if st.session_state.chat_history:
    st.markdown("---")
    st.subheader("Chat History")
    for q, a in st.session_state.chat_history:
        st.markdown(f"**You:** {q}")
        st.markdown(f"**Bot:** {a}")

