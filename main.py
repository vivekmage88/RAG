from fastapi import FastAPI
from schemas import AskRequest, AskResponse, Source
from answer import answer_question
from cache import get_cached_answer

app = FastAPI(title="Document RAG API", version="1.0.0")

@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest):
    was_cached = get_cached_answer(payload.question, payload.n_results, payload.max_distance) is not None
    
    result = answer_question(
        question=payload.question,
        n_results=payload.n_results,
        max_distance=payload.max_distance,
    )
    
    return AskResponse(**result)