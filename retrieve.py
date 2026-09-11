from store import collection, embed_texts

MAX_DISTANCE = 1.2

def search(question: str, n_result:int = 5):
    vector_search = embed_texts([question])[0]
    results = collection.query(
        query_embeddings=[vector_search],
        n_results=n_result,
        include=['documents', 'metadatas', 'distances']
    )
    return results

def search_relevant(question:str, n_results: int = 5, max_distance: float = MAX_DISTANCE):
    results = search(question, n_results)
    
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