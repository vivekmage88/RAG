import json
from ingest import extract_pages, clean

def find_questions(text: str) -> list[str]:
    questions = []
    for line in text.split("\n"):
        trimmed = line.strip()
        if trimmed.startswith("-") and trimmed.endswith("?"):
            questions.append(trimmed.lstrip("- ").strip())
    return questions

def build_golden_set(path:str):
    
    cases = []
    for page_num, raw in extract_pages(path):
        for question in find_questions(clean(raw)):
            cases.append({"question": question, "expected_page": page_num})
    return cases