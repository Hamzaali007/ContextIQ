from nemoguardrails import RailsConfig , LLMRails
from config import settings
from typing import Optional
_rails_instance = None

def get_rails() -> LLMRails:
    global _rails_instance
    if _rails_instance is None:
        config = RailsConfig.from_path("guardrails")
        _rails_instance = LLMRails(config)

    return _rails_instance


def _extract_content(response) -> str:
    """
    Handles both possible response shapes from rails.generate():
    - plain dict with "content" key (no options passed)
    - GenerationResponse object with .response = [{"role": ..., "content": ...}] (when options passed)
    """
    # Case 1: plain dict with "content"
    if isinstance(response, dict):
        if "content" in response:
            return response["content"]
        return str(response)

    # Case 2: GenerationResponse-like object with a "response" attribute
    messages = getattr(response, "response", None)
    if isinstance(messages, list) and messages:
        last = messages[-1]
        if isinstance(last, dict):
            return last.get("content", "")
        return str(last)

    return str(response)


def check_input(user_message: str) -> dict:
    rails = get_rails()
    response = rails.generate(
        messages=[{"role": "user", "content": user_message}],
        options={"rails": ["input"]},
    )
    content = _extract_content(response)

    refusal_markers = ["can't respond to that", "not able to answer that", "i'm sorry"]
    blocked = any(marker in content.lower() for marker in refusal_markers)

    return {
        "allowed": not blocked,
        "refusal_message": content if blocked else None,
    }


def check_output(bot_message: str) -> dict:
    rails = get_rails()
    response = rails.generate(
        messages=[
            {"role": "user", "content": "check"},
            {"role": "assistant", "content": bot_message},
        ],
        options={"rails": ["output"]},
    )
    content = _extract_content(response)

    refusal_markers = ["can't respond to that", "not able to answer that"]
    blocked = any(marker in content.lower() for marker in refusal_markers)

    return {
        "allowed": not blocked,
        "message": bot_message if not blocked else "This response was flagged and cannot be shown.",
    }


def guarded_answer(question:str,source:str,chat_history:list[dict] | None =None,session_id:str | None=None)-> dict:
    """Non-streaming version-kept for quiz/definitions/anywhere yuo need the full text upfront"""
    from llm.qa import answer_question
    input_check = check_input(question)
    if not input_check["allowed"]:
        return {"answer": input_check["refusal_message"],"sources":[]}

    result = answer_question(question=question,source=source,chat_history=chat_history,session_id=session_id)
    output_check = check_output(result["answer"])
    if not output_check["allowed"]:
        return {"answer":output_check["message"],"sources":[]}

    return result



def guarded_answer_stream(question:str,source:str,chat_history:list[dict] | None=None,session_id:str | None=None):
    """
    Streaming version. Input is checked before any generation starts.
    The output-check runs after the full answer has streamed (can't check text that doesn;t exist yet) 
    call the returned post_check after consuming the generator and show its result as a flag if blocked.
    Returns : (sources,generator,post check fn)
    """
    from llm.qa import answer_question_stream
    input_check = check_input(question)
    if not input_check["allowed"]:
        def _refusal():
            yield input_check["refusal_message"]

        return [], _refusal(), None

    sources, generator = answer_question_stream(question,source,chat_history=chat_history,session_id=session_id)
    full_text = {"value":""}

    def _wrapped():
        for chunk in generator:
            full_text["value"] +=chunk
            yield chunk

    def _post_check():
        return check_output(full_text["value"])

    return sources,_wrapped(),_post_check




def guarded_quiz(
    source: str,
    start_page: int,
    end_page: int,
    num_questions: int = 8,
    question_types: Optional[list[str]] = None,
    difficulty: Optional[str] = None,
    session_id: str | None = None,
) -> dict:
    from llm.quiz import generate_quiz

    input_check = check_input(f"Generate a quiz for pages {start_page}-{end_page}")
    if not input_check["allowed"]:
        return {"error": input_check["refusal_message"]}

    return generate_quiz(
        source=source,
        start_page=start_page,
        end_page=end_page,
        num_questions=num_questions,
        question_types=question_types,
        difficulty=difficulty,
        session_id=session_id,
    )

def guarded_definitions_by_range(source:str,start_page:int,end_page:int,session_id:str | None=None) -> dict:
    from llm.definitions import extract_definitions_by_range
    input_check = check_input(f"Extract definitions from pages {start_page}- {end_page}")
    if not input_check["allowed"]:
        return {"error":input_check["refusal_message"]}

    return extract_definitions_by_range(source=source,start_page=start_page,end_page=end_page,session_id=session_id)


def guarded_definitions_by_topic(source:str,topic:str,session_id:str | None=None)->dict:
    from llm.definitions import extract_definitions_by_topic

    input_check = check_input(topic)
    if not input_check["allowed"]:
        return {"error":input_check["refusal_message"]}

    return extract_definitions_by_topic(source=source,topic=topic,session_id=session_id)



def guarded_flashcards_by_range(source:str,start_page:int,end_page:int,num_cards:int | None=None,session_id:str | None=None) -> dict:
    from llm.Flashcards import generate_flashcards_by_range
    input_check = check_input(f"Generate flashcards for pages {start_page}-{end_page}")
    if not input_check["allowed"]:
        return {"error":input_check["refusal_message"]}
    return generate_flashcards_by_range(source=source,start_page=start_page,end_page=end_page,num_cards=num_cards,session_id=session_id)


def guarded_flashcards_by_topic(source:str,topic:str,num_cards:int | None=None,session_id:str | None=None)->dict:
    from llm.Flashcards import generate_flashcards_by_topic
    input_check = check_input(topic)
    if not input_check["allowed"]:
        return {"error":input_check["refusal_message"]}
    return generate_flashcards_by_topic(source=source,topic=topic,num_cards=num_cards,session_id=session_id)
