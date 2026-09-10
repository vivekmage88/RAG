import re
import hashlib
from dataclasses import dataclass
from pypdf import PdfReader

@dataclass
class Chunk:
    text: str
    doc_id: str
    doc_title:str
    page:int
    heading:str
    
    def chunk_id(self):
        return f"{self.doc_id}: p{self.page}"
    


BOILERPLATE = [
    re.compile(r"^FastAPI RAG Reference \| \d+/\d+$", re.M),
    re.compile(r"^FASTAPI-RAG-\d+ \| Page \d+ of \d+$", re.M),
    re.compile(r"^PAGE-ID: [A-Z0-9\-]+$", re.M),
    re.compile(r"^Original reference-style content.*$", re.M),
    re.compile(r"^Synthetic FastAPI learning material.*$", re.M),
]

def clean(text:str):
    for pattern in BOILERPLATE:
        text = pattern.sub("", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()

def extract_pages(path: str):
    reader = PdfReader(path)
    pages = []
    
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append((page_num, text))
        else:
            print(f"Page {page_num}: no text found, skipped")
    
    return pages

def split_heading_and_body(text:str):
    parts = text.split('\n', 1)
    heading = parts[0].strip()
    body = parts[1].strip() if len(parts) > 1 else ""
    return heading, body

def build_chunks(path:str, doc_title:str):
    doc_id = hashlib.sha256(doc_title.encode()).hexdigest()[:12]
    chunks = []
    
    for page_num, raw_text in extract_pages(path):
        cleaned = clean(raw_text)
        if not cleaned:
            continue
        heading, body = split_heading_and_body(cleaned)
        text_with_header = f"{doc_title} - {heading}\n\n{body}"
        
        chunk = Chunk(
                text=text_with_header,
                doc_id=doc_id,
                doc_title=doc_title,
                page=page_num,
                heading=heading,
            )
        chunks.append(chunk)
    
    return chunks

if __name__ == "__main__":
    chunks = build_chunks("fastapi.pdf", "FastAPI RAG Reference")
    print(f"{len(chunks)} chunks")

    first = chunks[0]
    print(f"\nid: {first.chunk_id()}")
    print(f"page: {first.page}")
    print(f"heading: {first.heading}")
    print(f"\ntext starts:\n{first.text[:200]}")
    
    # raw = pages[0][1]
    # cleaned = clean(raw)
    # print(f"\nBefore: {len(raw)} chars")
    # print(f"After: {len(cleaned)} chars")
    # print(f"\n{repr(cleaned[:300])}")
    