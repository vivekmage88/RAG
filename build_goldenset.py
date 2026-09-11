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


if __name__ == "__main__":
    cases = build_golden_set("fastapi.pdf")

    with open("golden_set.json", "w") as f:
        json.dump(cases, f, indent=2)

    print(f"{len(cases)} test cases written to golden_set.json")