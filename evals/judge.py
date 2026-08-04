import json
from llm.groq_client import generate_completion

JUDGE_SYSTEM_PROMPT = """You are an evaluation judge for a RAG (retrieval-augmented generation) system.
You will be given a question, the expected key facts, and the system's actual answer.
Score the answer on three dimensions, each 1-5 (5=best):
-faithfulness: Is the answer grounded in reasonable textbook content, with no fabricated facts?
-relevance: Does the answer actually address the question asked?
-correctness: Does the answer contain the expected key facts (or, for negative/off topic test cases, does it correctly decline  rather than hallucinate an answer)?
Return ONLY valid JSON, no markdown, no extra text:
{"faithfulness":1-5,"relevance":1-5,"correctness":1-5,"reasoning": "one sentence"}
"""


def judge_answer(question:str,expected_facts: list[str],actual_answer:str, is_negative_case: bool=False) -> dict:
    facts_Str = ", ".join(expected_facts)
    negative_note = (
        "\nNOTE: This is a negative test case- the question is OFF-TOPIC for the textbook."
        "A correct answer should decline to answer or say the info isn't in the document."
        if is_negative_case else ""
    )
    prompt = f""" Question: {question}
Expected key facts: {facts_Str}{negative_note}System's actual answer:
{actual_answer}

Score this answer per the rubric."""

    raw = generate_completion(prompt=prompt, system_prompt=JUDGE_SYSTEM_PROMPT, temperature=0.0)

    cleaned = raw.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]

        cleaned = cleaned.strip()


    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"faithfulness": None, "relevance": None, "correctness": None, "reasoning": f"Failed to parse JSON from judge output: {cleaned}"}
    

