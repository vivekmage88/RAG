# Document RAG API

A retrieval-augmented generation service over PDF documents. Upload a PDF, ask questions in natural language, get answers grounded in the document with page-number citations.

Built with FastAPI, ChromaDB, Redis and the OpenAI API.

---

## What it does

- **Ingests PDFs** — extracts text per page, strips repeating headers and footers, attaches a contextual header to each chunk
- **Answers questions** with citations back to the source page
- **Refuses to guess** — a distance threshold gates retrieval, and when nothing relevant is found the LLM is never called
- **Caches at two levels** — question embeddings and full answers, with invalidation by document version
- **Supports multiple documents** — retrieval can be scoped to a single document
- **Measures itself** — a 90-question golden set scores retrieval with MRR and precision@k

---

## Retrieval quality

Measured against a 90-question golden set built from the source document.

| Metric | Score |
|---|---|
| Precision@1 | 0.900 |
| Recall@5 | 1.000 |
| MRR | 0.945 |

The golden-set questions were generated from the pages they test, so they share vocabulary with their answers. These numbers are an optimistic baseline useful for comparing configurations, not an absolute measure of quality.

**Measured A/B — contextual headers:**

| Configuration | Precision@1 | Recall@5 | MRR |
|---|---|---|---|
| With contextual header | 0.900 | 1.000 | 0.945 |
| Body text only | 0.844 | 1.000 | 0.919 |

Prepending the document title and section heading to each chunk is worth 5.6 points of precision@1. Recall is unchanged, so the header improves ranking rather than finding.

---

## Architecture

```
ingest.py ──> store.py ──> ChromaDB
                              │
                              v
                         retrieve.py
                          │        │
                          v        v
                    answer.py   evaluate.py
```

The top row runs once per document. The bottom half runs on every question. ChromaDB is the only thing the two halves share, so they can be developed and tested independently.

| File | Responsibility |
|---|---|
| `ingest.py` | PDF to cleaned, headed chunks |
| `store.py` | Batched embedding, idempotent upsert |
| `retrieve.py` | Vector search, relevance gate, embedding cache |
| `answer.py` | Context assembly, LLM call, answer cache |
| `cache.py` | Redis layer, key construction, version invalidation |
| `evaluate.py` | Offline retrieval scoring |
| `main.py` | FastAPI endpoints |
| `schemas.py` | Request and response models |

---

## Setup

Requires Python 3.12, Redis, and an OpenAI API key.

```bash
git clone <repo-url>
cd doc-rag

python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# add your OPENAI_API_KEY to .env

brew services start redis
uvicorn main:app --reload
```

Interactive API docs at `http://127.0.0.1:8000/docs`.

---

## API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `POST` | `/documents` | Upload and index a PDF |
| `GET` | `/documents` | List indexed documents |
| `DELETE` | `/documents/{doc_id}` | Remove a document and its chunks |
| `POST` | `/ask` | Ask a question, get a cited answer |

### Upload a document

```bash
curl -X POST http://127.0.0.1:8000/documents \
  -F "file=@yourfile.pdf" \
  -F "doc_title=Your Document Title"
```

```json
{
  "doc_id": "acfb66efbb08",
  "doc_title": "Your Document Title",
  "pages": 30,
  "chunks_indexed": 30
}
```

### Ask a question

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "how do background tasks work?", "doc_id": "acfb66efbb08"}'
```

```json
{
  "answer": "BackgroundTasks can schedule small pieces of work to run after the response is sent (p17).",
  "sources": [
    {
      "page": 17,
      "heading": "Background Tasks After Returning a Response",
      "distance": 0.935
    }
  ],
  "cached": false
}
```

`doc_id` is optional. Omit it to search across every indexed document.

### Run the evaluation

```bash
python build_goldenset.py   # writes golden_set.json
python evaluate.py
```

---

## Design decisions

**Chunk per page, not per token budget.** The source document has one topic per page with its own heading, so the page boundary is already the semantic boundary. An earlier attempt to reconstruct paragraphs from PDF line-wrapping used punctuation and line-length heuristics, grew unreadable, and shattered code blocks into fragments. Documents with several topics per page would need genuine token-budget splitting with overlap.

**Contextual headers on every chunk.** Each chunk is prefixed with the document title and section heading before embedding, so a chunk that would otherwise start mid-topic carries its own context. Measured at 5.6 points of precision@1.

**Distance gate before the LLM call.** Vector search always returns the requested number of results — there is no empty result and no "no match" signal. Without a threshold, an out-of-domain question returns irrelevant chunks and the model answers from them fluently. When nothing passes the gate, the endpoint returns a fallback and the LLM is never called: no cost, no latency, no hallucination from empty context.

**Two caches with different lifetimes.** An embedding is a pure function of text and model, so it can be cached for a week. An answer depends on what is currently indexed, so it expires in an hour. Cache lifetime matches how quickly the underlying data goes stale.

**Cache invalidation by version, not deletion.** Cache keys are hashed, so there is no way to find every key belonging to a document. Instead a per-document counter is included in the key; incrementing it makes every old key unreachable in one operation, and they expire on their own TTL. Making old entries unreachable is cheaper than finding and deleting them.

**Caches fail open.** Every Redis call is wrapped, and a failure returns a cache miss. If Redis is down the service degrades in performance, not availability. A cache is an optimisation, never a dependency.

**Idempotent ingestion.** Chunk IDs are `sha256(doc_title)[:12] + ":p" + page` — deterministic from inputs that do not change, so re-ingesting a document overwrites rather than duplicating.

**Upload validated by magic bytes, not filename.** A real PDF begins with `%PDF`. Filenames are also sanitised with `os.path.basename` and a character whitelist to prevent path traversal.

---

## Known limitations

- **Ingestion blocks the request.** A large PDF holds the HTTP connection for the duration of embedding. Production would accept the upload, return 202 with a job ID, and process it in a background worker.
- **Boilerplate patterns are document-specific.** The header and footer regexes match one document's exact strings. A generic approach would detect lines appearing on most pages and strip them automatically.
- **Evaluation scores retrieval only.** It measures whether the correct page was found and how it ranked, not whether the generated answer was correct or its citations accurate.
- **Unscoped questions cannot be version-invalidated.** A question with no `doc_id` spans every document, so no single version applies. A global version counter would close this.
- **No deduplication at ingestion.** Indexing the same content under two titles stores it twice, and both copies compete for retrieval slots.
- **Scanned pages are skipped.** Image-only pages produce no extractable text; they are logged and ignored rather than passed through OCR.
- **`GET /documents` loads all metadata to count chunks.** Fine at this scale, wasteful at scale. Document-level records belong in a relational store.
