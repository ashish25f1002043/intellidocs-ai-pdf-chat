from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypdf import PdfReader
import google.generativeai as genai

import shutil
import os
from dotenv import load_dotenv

# ======================
# LOAD ENV
# ======================
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print("API KEY LOADED")

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")

# ======================
# FASTAPI APP
# ======================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================
# STORAGE
# ======================
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

pdf_text = ""   # store full pdf text only (NO embeddings)

# ======================
# REQUEST MODEL
# ======================
class QuestionRequest(BaseModel):
    question: str

# ======================
# HOME
# ======================
@app.get("/")
def home():
    return {"message": "Gemini PDF Chat Running 🚀"}

# ======================
# UPLOAD PDF
# ======================
@app.post("/upload")
def upload_pdf(file: UploadFile = File(...)):

    global pdf_text

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    reader = PdfReader(file_path)

    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    if not text.strip():
        return {"error": "No readable text found"}

    pdf_text = text   # store full text

    return {
        "message": "PDF uploaded successfully",
        "chars": len(pdf_text)
    }

# ======================
# ASK QUESTION
# ======================
@app.post("/ask")
def ask_question(req: QuestionRequest):

    global pdf_text

    try:

        if not pdf_text:
            return {"error": "Upload PDF first"}

        prompt = f"""
You are an intelligent AI PDF assistant.

Answer the question ONLY using the document below.

If answer is not present, say:
"The answer could not be found in the uploaded document."

---

DOCUMENT:
{pdf_text}

---

QUESTION:
{req.question}

---

ANSWER:
"""

        response = model.generate_content(prompt)

        return {
            "answer": response.text
        }

    except Exception as e:
        return {"error": str(e)}
