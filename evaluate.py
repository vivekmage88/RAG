import json
from retrieve import search


def evaluate(cases: list[dict], n_results: int = 5) -> dict:
    reciprocal_ranks = []
    hits_at_1 = 0
    hits_at_k = 0

    for case in cases:
        results = search(case["question"], n_results)

        pages = []
        for meta in results["metadatas"][0]:
            pages.append(meta["page"])

        rank = 0
        for position, page in enumerate(pages, start=1):
            if page == case["expected_page"]:
                rank = position
                break

        if rank == 1:
            hits_at_1 += 1

        if rank > 0:
            hits_at_k += 1
            reciprocal_ranks.append(1 / rank)
        else:
            reciprocal_ranks.append(0.0)

    total = len(cases)
    return {
        "cases": total,
        "precision_at_1": round(hits_at_1 / total, 3),
        "recall_at_k": round(hits_at_k / total, 3),
        "mrr": round(sum(reciprocal_ranks) / total, 3),
    }