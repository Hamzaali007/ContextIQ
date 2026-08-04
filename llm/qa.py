from vectorstore import search
from llm.groq_client import generate_completion
import json

QA_SYSTEM_PROMPT = """
You are ContextIQ, an educational assistant that helps students understand their uploaded textbook.

Rules:
-Answer ONLY using the provided context below. Do not use outside knowledge.
-If the answer is not present in the context, say clearly: "I couldn't find this in the document."
-Be concise and accurate. Cite the page number(s) your answer comes from when possible.
-Do not make up facts, page numbers, or details not present in the context.
-NEVER generate quizzes, test questions, or Q&A lists in your response. If the user asks for a quiz, test, or questions, reply ONLY with: "Please use the **Quiz Me** button at the top of the page to take an interactive quiz — it will grade your answers without showing them upfront!"
-Do NOT reveal answers to potential quiz questions. Your job is to explain concepts, not to test.
-Give fully structured answers which are easier to understand.
"""

FOLLOW_UP_SYSTEM_PROMPT = """ Given a question and its answer from a textbook Q&A session, suggest 3 short,
natural follow-up questions a student might reasonably ask next- questions that dig deeper into the 
same topic or a closely related one covered in the same context.

Return ONLY a JSON list of 3 short question strings, no markdown, no extra text.
Example : ["What causes this process to speed up?","How does this compare to X?","Why is this important?"]
"""
def generate_follow_up_questions(question:str,answer:str,n:int=3) -> list[str]:
    from llm.groq_client import generate_completion
    try:
        prompt = f"Question: {question}\n\n Answer: {answer}\n\n Suggest {n} folow-up questions."
        raw = generate_completion(prompt=prompt,system_prompt=FOLLOW_UP_SYSTEM_PROMPT,temperature=0.7)
        cleaned = raw.strip()

        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]

            cleaned  = cleaned.strip()
        parsed = json.loads(cleaned)
        if isinstance(parsed,list):
            return [str(q) for q in parsed[:n]]
        return []

    except Exception:
        return []


def build_context_block(chunks:list[dict]) -> str:
    """Format retrieved chunks into a labeled context block for the LLM"""
    parts = []
    for c in chunks:
        parts.append(f"[Page {c['page']}]\n {c['text']}")

    return "\n\n---\n\n".join(parts)



def build_history_block(chat_history:list[dict]| None) -> str:
    """Chat_History : list of {"question":str,"answer":str}, most recent last."""
    if not chat_history:
        return ""

    recent = chat_history[-3:]
    lines = [f"Q:{h['question']}\n A: {h['answer']}" for h in recent]
    return "Previous Conversation:\n" + "\n\n".join(lines) + "\n\n"



def answer_question(question:str,source:str,top_k:int=5,chat_history:list[dict] | None =None) -> dict:
    chunks = search(query=question,source=source,top_k=top_k)

    if not chunks:
        return {"answer":"I couldn't find any relevant content in this document.","sources":[]}

    context = build_context_block(chunks=chunks)
    history_block = build_history_block(chat_history)
    prompt = f"""{history_block} Context from the textbook:
    {context}

---
Student's question : {question}

Answer the question using only the context above"""
    answer = generate_completion(prompt=prompt,system_prompt=QA_SYSTEM_PROMPT,temperature=0.2)

    return {
        "answer":answer,
        "sources":[{"page":c["page"],"score":c["score"],"text":c["text"][:300]} for c in chunks],

    }

def answer_question_stream(question:str,source:str,top_k:int=5,chat_history:list[dict] | None =None):
    """
    Returns (sources,generator). Retrieval happens synchronously (fast);
    the generator yields the answer text chunk by chunk.
    """

    from llm.groq_client import generate_completion_stream
    chunks = search(query=question,source=source,top_k=top_k)
    sources = [{"page":c["page"],"score":c["score"],"text":c["text"]} for c in chunks]

    if not chunks:
        def _empty():
            yield "I couldn't find any relevant content in this document."

        return sources, _empty()

    context = build_context_block(chunks)
    history_block = build_history_block(chat_history)

    prompt = f"""{history_block} Context from the textbook:
    {context}
---
Student's question: {question}
Answer the question using only the context above.
    """

    generator = generate_completion_stream(prompt=prompt,system_prompt=QA_SYSTEM_PROMPT,temperature=0.2)
    return sources, generator



