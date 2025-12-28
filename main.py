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
    st.error("⚠️ OPENROUTER_API_KEY not found.")
    st.stop()

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="NextGen Coaching Institute AI Assistant",
    layout="centered"
)

# -----------------------------
# Custom Header
# -----------------------------
st.markdown("""
<style>
.chat-header {
    background: linear-gradient(90deg, #4285f4, #5a95f5);
    padding: 14px;
    color: white;
    font-size: 18px;
    font-weight: bold;
    border-radius: 10px;
}
</style>
<div class="chat-header">
    NextGen Coaching Institute AI Assistant
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Knowledge Directory
# -----------------------------
KNOWLEDGE_DIR = "knowledge_pdfs"
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
MAX_CONTEXT = 4500

# -----------------------------
# Session State
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! What can I help you with?"}
    ]

# -----------------------------
# Admin Sidebar (SECURE)
# -----------------------------
with st.sidebar:
    st.header("🔐 Admin Panel")
    admin_mode = st.checkbox("Enable Admin Mode")

    if admin_mode:
        password_input = st.text_input("Admin Password", type="password")

        if password_input != st.secrets["ADMIN_PASSWORD"]:
            st.warning("❌ Incorrect password")
            st.stop()

        st.success("✅ Admin access granted")

        uploaded_files = st.file_uploader(
            "Upload PDF(s)",
            type="pdf",
            accept_multiple_files=True
        )

        if uploaded_files:
            combined_text = ""
            for file in uploaded_files:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    combined_text += page.extract_text() or ""

                with open(os.path.join(KNOWLEDGE_DIR, file.name), "wb") as f:
                    f.write(file.getbuffer())

            combined_text = combined_text[:MAX_CONTEXT]
            with open("knowledge.txt", "w", encoding="utf-8") as f:
                f.write(combined_text)

            st.success("✅ Knowledge updated successfully")

# -----------------------------
# Load Knowledge
# -----------------------------
knowledge = ""
if os.path.exists("knowledge.txt"):
    with open("knowledge.txt", "r", encoding="utf-8") as f:
        knowledge = f.read()

# -----------------------------
# Display Chat
# -----------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------------
# Chat Input
# -----------------------------
user_input = st.chat_input("Message...")

if user_input:
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )

    with st.chat_message("user"):
        st.markdown(user_input)

    if not knowledge:
        bot_reply = "⚠️ Knowledge not available yet."
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
                        "You are an AI assistant that answers ONLY based on the provided document. "
                        "If the answer is not found, say: Information not available."
                    )
                },
                {
                    "role": "user",
                    "content": f"Document:\n{knowledge}\n\nQuestion:\n{user_input}"
                }
            ],
            "max_output_tokens": 200,
            "temperature": 0.2
        }

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                data = response.json()
                bot_reply = (
                    data["choices"][0]["message"]["content"]
                    if "choices" in data else
                    "Error generating response"
                )
                st.markdown(bot_reply)

    st.session_state.messages.append(
        {"role": "assistant", "content": bot_reply}
    )
