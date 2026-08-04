import json
from vectorstore import search_by_page_range, search
from llm.groq_client import generate_completion
from llm.utils import _limit_content   # <-- added import

ALL_DEFINITIONS_SYSTEM_PROMPT = """
You are ContextIQ, an educational assistant that extracts key terms and definitions from textbook content.
Rules:
-Scan the ENTIRE provided content and extract EVERY important term, policy name, or concept that is defined or explained - not just one. Aim for as many relevant terms as the content supports (typically 3-8 for a substantial passage).
-A term counts as "defined" if the content explains what it means, what it includes, or how it works - not only if it uses the exact phrase "is defined as".
-Only use terms and facts explicitly present in the provided content. Do not use outside knowledge.
-Keep each definition concise (1-2 sentences), in your own words.
-Include the page number where each term appears.
-Return ONLY valid JSON, no markdown, no backticks, no extra text.

JSON format:
{
  "definitions": [
    {"term": "...", "definition": "...", "page": 1}
  ]
}
"""

TARGETED_DEFINITION_SYSTEM_PROMPT = """
You are ContextIQ, an educational assistant that extracts specific term definitions from textbook content.
Rules:
-Extract ONLY the definition for the specific term or concept requested by the user.
-If the user asked for a single definition or a specific concept, return ONLY that definition (a single item in the definitions array). Do NOT extract unrelated terms.
-A term counts as "defined" if the content explains what it means, what it includes, or how it works.
-Only use terms and facts explicitly present in the provided content. Do not use outside knowledge.
-Keep the definition concise (1-2 sentences), in your own words.
-Include the page number where the term appears.
-Return ONLY valid JSON, no markdown, no backticks, no extra text.

JSON format:
{
  "definitions": [
    {"term": "...", "definition": "...", "page": 1}
  ]
}
"""

DEFINITIONS_SYSTEM_PROMPT = ALL_DEFINITIONS_SYSTEM_PROMPT


def _normalize_definitions(data: dict) -> dict:
    """Defensively normalize key-name drift, same pattern as quiz.py"""
    items = data.get("definitions") or data.get("terms") or []
    if isinstance(items, dict):
        items = [items]

    normalized = []
    for d in items:
        if not isinstance(d, dict):
            continue
        normalized.append({
            "term": d.get("term") or d.get("word") or "",
            "definition": d.get("definition") or d.get("meaning") or "",
            "page": d.get("page"),
        })

    return {"definitions": [d for d in normalized if d["term"] and d["definition"]]}


def extract_definitions_by_range(source: str, start_page: int, end_page: int) -> dict:
    """Extract key terms/definitions from a specific page range"""
    chunks = search_by_page_range(source=source, start_page=start_page, end_page=end_page)

    if not chunks:
        return {"error": f"No content found in pages {start_page} - {end_page} for this document."}

    return _run_extraction(chunks)


def extract_definitions_by_topic(source: str, topic: str, top_k: int = 5, min_score: float = 0.4) -> dict:
    """Extract key terms/definitions related to a topic via semantic search"""
    chunks = search(query=topic, source=source, top_k=top_k)

    relevant_chunks = [c for c in chunks if c["score"] >= min_score]

    if not relevant_chunks:
        return {"error": f"No sufficiently relevant content found for topic '{topic}' in this document."}

    return _run_extraction(relevant_chunks, target_topic=topic)


def _run_extraction(chunks: list[dict], target_topic: str | None = None) -> dict:
    # ---- REPLACED content join with _limit_content ----
    content, truncated = _limit_content(chunks)
    # ------------------------------------------------

    if target_topic:
        system_prompt = TARGETED_DEFINITION_SYSTEM_PROMPT
        prompt = f"""Content from the textbook:
{content}
---
The user specifically requested the definition for: "{target_topic}".
Extract ONLY the definition for "{target_topic}" (or the single requested concept).
Return the response as JSON matching the required format exactly.
"""
    else:
        system_prompt = ALL_DEFINITIONS_SYSTEM_PROMPT
        prompt = f"""Content from the textbook:
{content}
---
Extract all key terms and their definitions from this content.
Return the response as JSON matching the required format exactly.
"""

    raw_response = generate_completion(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=0.2,
    )
    cleaned = raw_response.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        raw_data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse definitions JSON: {e}", "raw_response": raw_response}

    definitions_data = _normalize_definitions(raw_data)

    if not definitions_data["definitions"]:
        return {"error": "No definitions could be extracted from this content.", "raw_response": raw_response}

    # ---- Add truncation note if applicable ----
    if truncated:
        definitions_data["note"] = "This page range was large, so definitions were extracted from the first portion of it to stay within model limits. Try a narrower range for full coverage."

    return definitions_data