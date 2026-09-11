import os
import time
from openai import OpenAI
from retrieve import search_relevant
from dotenv import load_dotenv
from cache import get_cached_answer, set_cached_answer

load_dotenv()

client = OpenAI(api_key=os.getenv(key="OPENAI_API_KEY"))
CHAT_MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """You answer questions about a technical document.

Use ONLY the context provided. Do not use outside knowledge.
Cite the page number for each claim, like this: (p17).
Answer from the context. Only say the document doesn't cover it if the context is genuinely unrelated to the question.
Never invent page numbers or facts."""


def generate_answer(question:str, context:str):
    completion = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
        temperature=0.1,
        max_tokens=400,
    )
    return completion.choices[0].message.content

def build_context(matches: list[dict]):
    parts = []
    
    for match in matches:
        header = f"[Page {match['page']} - {match['heading']}]"
        parts.append(f"{header}\n{match['text']}")
    return "\n\n---\n\n".join(parts)

# cache Answer
def answer_question(question: str, n_results: int = 5, max_distance: float = 1.2) -> dict:
    cached = get_cached_answer(question, n_results, max_distance)
    if cached is not None:
        cached["cached"] = True
        return cached

    matches = search_relevant(question, n_results, max_distance)

    if not matches:
        result = {
            "answer": "I couldn't find anything in the document about that.",
            "sources": [],
        }
    else:
        context = build_context(matches)
        answer = generate_answer(question, context)

        sources = []
        for match in matches:
            sources.append({
                "page": match["page"],
                "heading": match["heading"],
                "distance": match["distance"],
            })

        result = {"answer": answer, "sources": sources}

    set_cached_answer(question, n_results, max_distance, result)
    result["cached"] = True
    return result

# Test Phase
if __name__ == "__main__":
    q = "how do background tasks work?"

    start = time.perf_counter()
    first = answer_question(q)
    t1 = time.perf_counter() - start

    start = time.perf_counter()
    second = answer_question(q)
    t2 = time.perf_counter() - start

    print(f"first:  {t1:.3f}s")
    print(f"second: {t2:.3f}s")
    print(f"same answer: {first['answer'] == second['answer']}")