from fastapi import FastAPI, UploadFile, File, Query
from dotenv import load_dotenv
import os
import requests
import PyPDF2

# Load env
load_dotenv(dotenv_path=".env")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found")

app = FastAPI()

pdf_text = ""  # GLOBAL STORAGE

# ------------------ Upload PDF ------------------
@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    global pdf_text
    reader = PyPDF2.PdfReader(file.file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    pdf_text = text.strip()

    return {"message": "PDF uploaded successfully", "text_length": len(pdf_text)}

# ------------------ Ask Question ------------------
@app.post("/ask")
def ask_question(question: str = Query(...)):
    if not pdf_text:
        return {"error": "No PDF uploaded yet"}

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "allenai/olmo-3.1-32b-think:free",
        "messages": [
            {"role": "system", "content": "Answer using the uploaded PDF only."},
            {"role": "user", "content": f"PDF Content:\n{pdf_text}\n\nQuestion:\n{question}"}
        ]
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload
    )

    data = response.json()

    if "choices" not in data:
        return {"error": data}

    return {"answer": data["choices"][0]["message"]["content"]}
