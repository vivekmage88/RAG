import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv(key="OPENAI_API_KEY"))
CHAT_MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """You answer questions about a technical document.

Use ONLY the context provided. Do not use outside knowledge.
Cite the page number for each claim, like this: (p17).
If the context does not contain the answer, say so plainly.
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


def answer_question(question: str) -> dict:
    from retrieve import search_relevant

    matches = search_relevant(question)

    if not matches:
        return {
            "answer": "I couldn't find anything in the document about that.",
            "sources": [],
        }

    context = build_context(matches)
    answer = generate_answer(question, context)

    sources = []
    for match in matches:
        sources.append({
            "page": match["page"],
            "heading": match["heading"],
            "distance": match["distance"],
        })

    return {"answer": answer, "sources": sources}

# Test Phase
if __name__ == "__main__":
    result = answer_question("what is FastAPI built on top of?")
    print(result["answer"])
    print(result["sources"])