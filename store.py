import os
import chromadb
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

chroma = chromadb.PersistentClient(path='./chroma_data')
collection = chroma.get_or_create_collection('documents')


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
EMBED_MODEL = "text-embedding-3-small"

def embed_texts(text:list[str]):
    response = client.embeddings.create(model=EMBED_MODEL, input=text)
    vector = []
    
    for item in response.data:
        vector.append(item.embedding)
    
    return vector

def embed_in_batches(text:list[str], batch_size: int = 50):
    all_vectors = []
    
    for start in range(0, len(text), batch_size):
        batch = text[start:start+batch_size]
        vectors = embed_texts(batch)
        all_vectors.extend(vectors)
        print(f"Embedded {len(all_vectors)}/{len(text)}")
    
    return all_vectors



# chromadb section

def store_chunks(chunks):
    texts = []
    ids = []
    metadatas = []
    
    for chunk in chunks:
        texts.append(chunk.text)
        ids.append(chunk.chunk_id())
        metadatas.append({
            "doc_id": chunk.doc_id,
            "doc_title": chunk.doc_title,
            "page": chunk.page,
            "heading": chunk.heading,
        })
        
    vectors = embed_in_batches(texts)
    
    collection.upsert(
        ids=ids,
        embeddings= vectors,
        documents=texts,
        metadatas=metadatas
    )
    return len(chunks)


# Test case

if __name__ == "__main__":
    from ingest import build_chunks

    chunks = build_chunks("fastapi.pdf", "FastAPI RAG Reference")
    count = store_chunks(chunks)
    print(f"Stored {count} chunks")
    print(f"Collection holds {collection.count()} items")