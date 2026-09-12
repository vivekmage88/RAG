from store import collection, embed_texts
from cache import get_cached_embedding, set_cached_embedding

MAX_DISTANCE = 1.2

# calling Cache function


def get_query_vector(question: str) -> list[float]:
    cached = get_cached_embedding(question)
    if cached is not None:
        return cached

    vector = embed_texts([question])[0]
    set_cached_embedding(question, vector)
    return vector

def search(question: str, n_results: int = 5, doc_id: str | None = None):
    query_vector = get_query_vector(question)

    where = None
    if doc_id is not None:
        where = {"doc_id": doc_id}

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=n_results,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    return results

def search_relevant(question:str, n_results: int = 5, max_distance: float = MAX_DISTANCE, doc_id = None):
    results = search(question, n_results, doc_id)
    
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distance = results["distances"][0]
    
    matches = []
    
    for i in range(len(documents)):
        if distance[i] <= max_distance:
            matches.append({
                "text": documents[i],
                "page": metadatas[i]["page"],
                "heading": metadatas[i]["heading"],
                "doc_title": metadatas[i]["doc_title"],
                "distance": round(distance[i], 3),
            })
    return matches    

# Testing Phase
if __name__ == "__main__":
    questions = [
        "how do I validate request bodies?",
        "what is FastAPI built on top of?",
        "how do background tasks work?",
        "what is the capital of France?",
    ]

    for question in questions:
        matches = search_relevant(question)
        print(f"\n{question}")

        if not matches:
            print("  no relevant matches")
            continue

        for match in matches:
            print(f"  {match['distance']}  p{match['page']}  {match['heading']}")