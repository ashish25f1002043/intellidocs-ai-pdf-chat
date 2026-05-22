from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

import google.generativeai as genai

import shutil
import os
import numpy as np
from dotenv import load_dotenv

# ======================
# LOAD ENV
# ======================
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print("API KEY:", GEMINI_API_KEY)

genai.configure(api_key=GEMINI_API_KEY)


model = genai.GenerativeModel("gemini-2.5-flash")

# ======================
# FASTAPI
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

# ======================
# EMBEDDING MODEL
# ======================
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# ======================
# MEMORY
# ======================
pdf_chunks = []
pdf_embeddings = None

# ======================
# REQUEST MODEL
# ======================
class QuestionRequest(BaseModel):
    question: str

# ======================
# CHUNK FUNCTION
# ======================
def chunk_text(text, chunk_size=250, overlap=50):

    words = text.split()

    chunks = []

    step = chunk_size - overlap

    for i in range(0, len(words), step):

        chunk = " ".join(words[i:i + chunk_size])

        chunks.append(chunk)

    return chunks

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

    global pdf_chunks
    global pdf_embeddings

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:
        text += page.extract_text() or ""

    if not text.strip():
        return {"error": "No readable text found"}

    pdf_chunks = chunk_text(text)

    pdf_embeddings = embedder.encode(pdf_chunks)
    pdf_embeddings = np.array(pdf_embeddings)

    return {
        "message": "PDF uploaded successfully",
        "chunks": len(pdf_chunks)
    }

# ======================
# ASK QUESTION
# ======================
@app.post("/ask")
def ask_question(req: QuestionRequest):

    global pdf_chunks
    global pdf_embeddings

    try:

        if pdf_embeddings is None:
            return {"error": "Upload PDF first"}

        question = req.question

        q_embedding = embedder.encode(question)

        scores = np.dot(pdf_embeddings, q_embedding)

        top_indexes = np.argsort(scores)[-4:]

        context = "\n\n".join([pdf_chunks[i] for i in top_indexes])

        prompt = f"""
You are an intelligent AI PDF assistant.

Your task is to answer the user's question using ONLY the provided document context.

Instructions:
- Read the context carefully.
- Give clear, accurate, and well-structured answers.
- Keep responses concise but informative.
- If the answer is partially available, provide the closest relevant explanation.
- If the answer is completely unavailable in the context, respond with:
  "The answer could not be found in the uploaded document."
- Use bullet points when suitable.
- Explain difficult concepts in simple language.
- Maintain a professional and helpful tone.

Document Context:
{context}

User Question:
{question}

Answer:
"""

        response = model.generate_content(prompt)

        return {
            "answer": response.text,
            "context": context
        }

    except Exception as e:
        return {"error": str(e)}