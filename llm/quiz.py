import json
from typing import Optional
from vectorstore import search_by_page_range
from llm.groq_client import generate_completion
from llm.utils import _limit_content

# Base system prompt – we'll replace the type instruction later
QUIZ_SYSTEM_PROMPT_BASE = """You are ContextIQ, an educational assistant that creates test papers from textbook content.

Rules:
- Generate questions ONLY from the provided content. Do not use outside knowledge.
- For multiple_choice: include exactly 4 options and correct_answer as "A"/"B"/"C"/"D".
- For true_false: options must be ["True", "False"] and correct_answer is "True" or "False".
- For short_answer and definition: do NOT include an options field. Provide correct_answer as the expected answer text (a brief phrase or 1-2 sentences).
- For long_answer: do NOT include an options field. This is an essay/detailed-response question expecting a multi-sentence, paragraph-length answer. Provide correct_answer as a model answer covering the key points expected.
- Include a brief explanation for every question.
- Return ONLY valid JSON. No markdown, no backticks, no extra text before or after the JSON.
- Use these EXACT key names: "questions" (top-level list), and within each item: "type", "question", "options" (if applicable), "correct_answer", "explanation".

Example of correct format:
{
  "questions": [
    {
      "type": "multiple_choice",
      "question": "What is the standard working week?",
      "options": ["A. 30 hours", "B. 40 hours", "C. 45 hours", "D. 50 hours"],
      "correct_answer": "B",
      "explanation": "The document states standard hours are 40 per week."
    },
    {
      "type": "short_answer",
      "question": "How many sick days are provided annually?",
      "correct_answer": "8 days",
      "explanation": "Section 3.2 states employees receive 8 sick days per year."
    },
    {
      "type": "true_false",
      "question": "Remote work is available to all employees immediately upon hire.",
      "options": ["True", "False"],
      "correct_answer": "False",
      "explanation": "Employees must complete 90 days before applying for hybrid work."
    }
  ]
}
"""

def _infer_type(q: dict) -> str:
    explicit = q.get("type")
    if explicit:
        return explicit
    opts = q.get("options")
    if isinstance(opts, list):
        cleaned = {str(o).strip().lower() for o in opts}
        if cleaned and cleaned <= {"true", "false"}:
            return "true_false"
        if len(opts) == 4:
            return "multiple_choice"
    return "short_answer"


def _is_structurally_valid(q: dict) -> bool:
    qtype = q.get("type")
    opts = q.get("options")
    if not q.get("question") or not q.get("correct_answer"):
        return False
    if qtype == "multiple_choice":
        return isinstance(opts, list) and len(opts) == 4
    if qtype == "true_false":
        return isinstance(opts, list) and {str(o).strip().lower() for o in opts} <= {"true", "false"}
    if qtype in ("short_answer", "long_answer", "definition"):
        return True
    return False


def _normalize_quiz_data(data: dict) -> dict:
    questions = data.get("questions") or data.get("question") or []
    if isinstance(questions, dict):
        questions = [questions]

    normalized = []
    for q in questions:
        if not isinstance(q, dict):
            continue
        question_text = q.get("question") or q.get("questions") or q.get("text") or ""
        item = {
            "type": _infer_type(q),
            "question": question_text,
            "options": q.get("options"),
            "correct_answer": q.get("correct_answer") or q.get("answer"),
            "explanation": q.get("explanation", ""),
        }
        if _is_structurally_valid(item):
            normalized.append(item)

    return {"questions": normalized}

def generate_quiz(
    source: str,
    start_page: int,
    end_page: int,
    num_questions: int = 8,
    question_types: Optional[list[str]] = None,
    difficulty: Optional[str] = None,
    session_id: str | None = None,
) -> dict:
    chunks = search_by_page_range(source=source, start_page=start_page, end_page=end_page, session_id=session_id)
    if not chunks:
        return {"error": f"No content found in pages {start_page}-{end_page} for this document."}

    content, truncated = _limit_content(chunks)

    if question_types:
        types_str = " ,".join(question_types)
        type_instruction = f"Generate ONLY the following question types: {types_str}."
    else:
        type_instruction = "Use a MIX of these types: multiple_choice, short_answer, true_false, definition. Do not make every question multiple_choice."

    system_prompt = QUIZ_SYSTEM_PROMPT_BASE.replace(
        "Use a MIX of these types: multiple_choice, short_answer, true_false, definition. Do not make every question multiple_choice.",
        type_instruction
    )

    if difficulty:
        difficulty_instruction = f"Generate questions at a {difficulty} difficulty level."
    else:
        difficulty_instruction = "Generate questions at a moderate, well-balanced difficulty level."

    collected: list[dict] = []
    seen_question_texts: set[str] = set()
    max_attempts = 3
    attempt = 0
    last_raw_response = ""

    while len(collected) < num_questions and attempt < max_attempts:
        remaining = num_questions - len(collected)
        request_count = remaining * (2 + attempt)

        prompt = f"""Content from the textbook (pages {start_page}-{end_page}):

{content}

---

Generate exactly {request_count} test questions based on this content, using only the allowed types as instructed.
{difficulty_instruction}
Return the response as JSON matching the required format and exact key names."""

        raw_response = generate_completion(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.6,
        )
        last_raw_response = raw_response

        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()

        try:
            raw_data = json.loads(cleaned)
        except json.JSONDecodeError:
            attempt += 1
            continue

        quiz_data = _normalize_quiz_data(raw_data)
        questions = quiz_data["questions"]

        if question_types:
            allowed_types = set(question_types)
            questions = [q for q in questions if q.get("type") in allowed_types]

        for q in questions:
            qtext = q["question"].strip().lower()
            if qtext and qtext not in seen_question_texts:
                seen_question_texts.add(qtext)
                collected.append(q)
                if len(collected) >= num_questions:
                    break

        attempt += 1

    final_questions = collected[:num_questions]

    if not final_questions:
        return {
            "error": f"Could not generate any questions of types: {', '.join(question_types) if question_types else 'mixed'}.",
            "raw_response": last_raw_response,
        }

    
    result = {"questions": final_questions}
    if truncated:
        result["note"] = "This page range was large, so the quiz was generated from the first portion of it to stay within model limits. Try a narrower range for full coverage."  # type: ignore

    return result