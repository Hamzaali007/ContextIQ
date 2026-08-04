"""
Run all evals: python evals/run_eval.py
Requires: assets/sample_textbook.pdf already ingested under source "sample_textbook.pdf"
(see scripts/create_sample_pdf.py + ingest it once via the app or a quick script first).
"""

import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings  # noqa: triggers load_dotenv
from llm.qa import answer_question
from vectorstore import search
from evals.dataset import QA_EVAL_CASES
from evals.judge import judge_answer


def eval_retrieval_precision(case: dict, top_k: int = 5) -> dict:
    """Deterministic check: does the expected page show up in the top-k retrieved chunks?
    Skipped for negative (off-topic) cases, since there's no 'correct' page for those."""
    if case.get("is_negative_case"):
        return {"skipped": True}

    results = search(query=case["question"], source=case["source"], top_k=top_k)
    retrieved_pages = [r["page"] for r in results]
    hit = case["expected_page"] in retrieved_pages
    rank = retrieved_pages.index(case["expected_page"]) + 1 if hit else None

    return {"hit": hit, "rank": rank, "retrieved_pages": retrieved_pages}


def run_qa_eval() -> dict:
    results = []
    for case in QA_EVAL_CASES:
        retrieval_result = eval_retrieval_precision(case)

        answer_result = answer_question(question=case["question"], source=case["source"])
        answer_text = answer_result["answer"]

        judge_result = judge_answer(
            question=case["question"],
            expected_facts=case["expected_facts"],
            actual_answer=answer_text,
            is_negative_case=case.get("is_negative_case", False),
        )

        results.append({
            "question": case["question"],
            "answer": answer_text,
            "retrieval": retrieval_result,
            "judge": judge_result,
        })

    return results


def summarize(results: list[dict]) -> dict:
    scored = [r for r in results if r["judge"]["faithfulness"] is not None]
    n = len(scored)
    if n == 0:
        return {"error": "No results could be judged"}

    avg = lambda key: round(sum(r["judge"][key] for r in scored) / n, 2)

    retrieval_cases = [r for r in results if not r["retrieval"].get("skipped")]
    retrieval_hits = sum(1 for r in retrieval_cases if r["retrieval"]["hit"])
    retrieval_precision = round(retrieval_hits / len(retrieval_cases), 2) if retrieval_cases else None

    return {
        "n_cases": len(results),
        "n_judged": n,
        "avg_faithfulness": avg("faithfulness"),
        "avg_relevance": avg("relevance"),
        "avg_correctness": avg("correctness"),
        "retrieval_precision_at_5": retrieval_precision,
    }


if __name__ == "__main__":
    print("Running ContextIQ QA eval suite...\n")
    results = run_qa_eval()
    summary = summarize(results)

    print("=" * 50)
    print("SUMMARY")
    print("=" * 50)
    for k, v in summary.items():
        print(f"{k}: {v}")

    print("\n" + "=" * 50)
    print("PER-CASE DETAIL")
    print("=" * 50)
    for r in results:
        print(f"\nQ: {r['question']}")
        print(f"A: {r['answer'][:150]}...")
        print(f"Retrieval: {r['retrieval']}")
        print(f"Judge: {r['judge']}")

    os.makedirs("evals/results", exist_ok=True)
    out_path = f"evals/results/qa_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_path, "w") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2)
    print(f"\nFull report saved to {out_path}")