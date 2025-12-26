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

st.set_page_config(page_title="Custom AI Chatbot", layout="centered")
st.title("🤖 AI Assistant")

KNOWLEDGE_FILE = "knowledge.txt"
MAX_CONTEXT = 4000   # VERY IMPORTANT

# -----------------------------
# ADMIN MODE
# -----------------------------
admin_mode = st.checkbox("🔐 Admin Mode")

if admin_mode:
    uploaded_file = st.file_uploader("Upload training PDF", type="pdf")

    if uploaded_file:
        reader = PyPDF2.PdfReader(uploaded_file)
        text = ""

        for page in reader.pages:
            text += page.extract_text() or ""

        # LIMIT TEXT SIZE
        text = text[:MAX_CONTEXT]

        with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
            f.write(text)

        st.success("✅ Knowledge stored successfully")

# -----------------------------
# LOAD KNOWLEDGE
# -----------------------------
knowledge = ""
if os.path.exists(KNOWLEDGE_FILE):
    with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
        knowledge = f.read()

# -----------------------------
# CHAT
# -----------------------------
st.subheader("Ask a question")
question = st.text_input("Type your question")

if question:
    if not knowledge:
        st.warning("Admin must upload PDF first.")
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
                        "Answer ONLY from the provided knowledge. "
                        "If the answer is not found, say 'Information not available'. "
                        "Reply in 2–3 sentences."
                    )
                },
                {
                    "role": "user",
                    "content": f"Knowledge:\n{knowledge}\n\nQuestion:\n{question}"
                }
            ],
            "max_tokens": 150,
            "temperature": 0.2
        }

        with st.spinner("Thinking..."):
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )

            data = response.json()

            # DEBUG OUTPUT (TEMPORARY)
            if "error" in data:
                st.error(data["error"])
                st.json(data)
                st.stop()

            choices = data.get("choices", [])

            if choices and "message" in choices[0]:
                answer = choices[0]["message"].get("content")
                st.markdown("### 🤖 Answer")
                st.write(answer)
            else:
                st.error("⚠️ Model returned empty response")
                st.json(data)  # SHOW RAW RESPONSE
