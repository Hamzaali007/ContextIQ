import json
from vectorstore import search_by_page_range, search
from llm.groq_client import generate_completion
from llm.utils import _limit_content   # <-- import from utils

FLASHCARD_SYSTEM_PROMPT = """
You are ContextIQ, an educational assistant that creates flashcards from textbook content.
Rules:
-Scan the content and pull out anything worth memorizing: key facts, processes, numbers, dates, relationship, or defined terms- not ONLY formal definitions. A flashcard can ask
"What happens during X?" or "front" (a short question or prompt) and a "back" (the concise answer,
1-2 sentences, in your own words).
-Only use facts explicitly present in the provided content. Do not use outside knowledge.
-Include  the page number each card's info comes from.
-Aim for as many good cards as the content supports (typically 4-10 for a substantial passage),
unless a specific count is requested.
-Return ONLY valid JSON, no markdown, no backticks, no extra text.

JSON format:
{
"flashcard":[
{"front":"...", "back":"...","page":1}
]
}
"""

TARGETED_FLASHCARD_SYSTEM_PROMPT = """
You are ContextIQ, an educational assistant that creates flashcards from textbook content.
Rules:
-The user asked for flashcards about a SPECIFIC topic. Only create cards directly relevant
to that topic- do not include unrelated cards from the surrounding content.
-Each flashcard has a "front"  (a short question or prompt) and a "back" (the concise answer,
1-2 sentences, in your own words).
-A card can cover a fact, a process, a number , or a definition - whatever is most useful for 
memorizing this topic, not only formal definitions.
-Only use facts explicitly present in the provided content. Do not use outside knowledge.
-Include the page number each card's info comes from.
-Return ONLY valid JSON, no markdown, no backticks , no extra text.

JSON format:
{
"flashcards":[
{"front":"...","back":"...","page":1}
]}
"""

def _normalize_flashcards(data:dict)-> dict:
    items = data.get("flashcard") or data.get("cards") or []
    if isinstance(items,dict):
        items = [items]

    normalized = []
    for c in items:
        if not isinstance(c,dict):
            continue

        normalized.append({
            "front":c.get("front") or c.get("question") or c.get("term") or "",
            "back":c.get("back") or c.get("answer") or c.get("definition") or "",
            "page":c.get("page"),
        })

    return {"flashcards": [c for c in normalized if c["front"] and c["back"]]}


def generate_flashcards_by_range(source:str,start_page:int,end_page:int, num_cards:int | None=None)->dict :
    chunks = search_by_page_range(source=source,start_page=start_page,end_page=end_page)
    if not chunks:
        return {"error":f"No content found in pages {start_page} - {end_page} for this document."}

    return _run_generation(chunks,num_cards=num_cards)


def generate_flashcards_by_topic(source:str,topic:str,top_k:int=5,min_score:float=0.4,num_cards:int | None=None) -> dict:
    chunks = search(query=topic,source=source,top_k=top_k)
    relevant_chunks = [c for c in chunks if c["score"] >= min_score]

    if not relevant_chunks:
        return {"error":f"No sufficiently relevant content found for topic '{topic}' in this document."}

    return _run_generation(relevant_chunks,target_topic=topic,num_cards=num_cards)


def _run_generation(chunks: list[dict], target_topic: str | None = None, num_cards: int | None = None) -> dict:
    content, truncated = _limit_content(chunks)   # uses imported helper
    count_instruction = f"Create exactly {num_cards} flashcards." if num_cards else ""

    if target_topic :
        system_prompt = TARGETED_FLASHCARD_SYSTEM_PROMPT
        prompt = f""" Content from the textbook:
        {content}
---
The user specifically wants flashcards about: "{target_topic}".
{count_instruction}
Return the response as JSON matching the required format exactly.
"""    
    else:
        system_prompt = FLASHCARD_SYSTEM_PROMPT
        prompt = f""" Content from the textbook:
        {content}
---
Create flashcards covering the important info in this content.
{count_instruction}
Return the response as JSON matching the required format exactly
"""

    raw_response = generate_completion(prompt=prompt,system_prompt=system_prompt,temperature=0.4)

    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]

        cleaned = cleaned.strip()

    try:
        raw_data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse flashcard JSON: {e}","raw_response":raw_response}

    flashcard_data = _normalize_flashcards(raw_data)
    if num_cards:
        flashcard_data["flashcards"] = flashcard_data["flashcards"][:num_cards]

    if not flashcard_data["flashcards"]:
        return {"error":"No flashcards could be generated from this content.","raw_response":raw_response}

    if truncated:
        flashcard_data["note"] = "This page range was large, so flashcards were generated from the first portion of it to stay within model limits. Try a narrower range for full coverage."

    return flashcard_data