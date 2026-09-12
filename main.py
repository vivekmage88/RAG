import os
import re
from fastapi import FastAPI
from schemas import AskRequest, AskResponse, Source
from answer import answer_question
from cache import get_cached_answer
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from ingest import build_chunks
from store import store_chunks, collection

UPLOAD_DIR = "uploads"
MAX_UPLOAD_BYTES = 20 * 1024 * 1024      # 20 MB
PDF_MAGIC = b"%PDF"

app = FastAPI(title="Document RAG API", version="1.0.0")

@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest):
    
    result = answer_question(
        question=payload.question,
        n_results=payload.n_results,
        max_distance=payload.max_distance,
        doc_id=payload.doc_id,
    )
    
    return AskResponse(**result)

def safe_filename(name:str):
    base = os.path.basename(name)
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", base)
    return cleaned[:100]

# File Upload APi & Function

@app.post("/documents", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    doc_title: str = Form(...),
):
    contents = await file.read()

    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 20 MB")

    if not contents.startswith(PDF_MAGIC):
        raise HTTPException(status_code=400, detail="Not a PDF file")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    path = os.path.join(UPLOAD_DIR, safe_filename(file.filename))

    with open(path, "wb") as f:
        f.write(contents)

    chunks = build_chunks(path, doc_title)
    if not chunks:
        raise HTTPException(status_code=400, detail="No extractable text found")

    count = store_chunks(chunks)

    return {
        "doc_id": chunks[0].doc_id,
        "doc_title": doc_title,
        "pages": count,
        "chunks_indexed": count,
    }
# TestCase
if __name__ == "__main__":
    for name in ["report.pdf", "../../etc/passwd", "my file (1).pdf", "a" * 300 + ".pdf"]:
        print(f"{name[:40]!r:45} -> {safe_filename(name)!r}")
        
        print(collection.count())