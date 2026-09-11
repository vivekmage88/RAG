<div>
  <div>
    <h1>Document RAG System</h1>
Architecture, design decisions and evaluation
FastAPI · ChromaDB · OpenAI embeddings · PyPDF | Vivek Sharma</div>

<div>  
  <h3>WHAT IT DOES</h3>
  <p>A retrieval-augmented generation pipeline over a PDF document. It ingests a PDF, splits it into retrievable chunks, embeds them into
a vector store, and answers natural-language questions using only the retrieved content — returning page-number citations with
every answer. A separate evaluation harness measures retrieval quality against a labelled question set.</p>
  <div>
    <h3>MODULE ARCHITECTURE</h3>
    <img width="2720" height="2024" alt="doc_rag_module_architecture" src="https://github.com/user-attachments/assets/0b6e657f-c906-45f6-a886-28fc9f4d4d62" />
  </div>
  <div>
    <h3>INGESTION PIPELINE</h3>
    <p><strong>Extract :</strong> PyPDF returns text per page. Page number is attached here and carried through every later stag</p>
    <p><strong>Clean  :</strong> Repeating header and footer removed by regex; runs of spaces and newlines collapsed.</p>
    <p><strong>Split heading  :</strong> First line of the page is taken as the section title.</p>
    <p><strong>Build chunk  :</strong> Document title and heading prepended to the body as a contextual header.</p>
    <p><strong>Split Embed   :</strong>Batched calls to text-embedding-3-small , 1,536 dimensions per chunk.</p>
    <p><strong>Build Store   :</strong> Upsert into Chroma keyed on doc id:pN.</p>
  </div>

  <div>
    <h1>Cache layer Using Redish</h1>
    <h3>Cache ARCHITECTURE</h3>
    <img width="2720" height="2080" alt="rag_cache_decision_flow" src="https://github.com/user-attachments/assets/0f0bf721-9f68-4d40-a2fb-6e0bd3882770" />

    
  </div>
  
