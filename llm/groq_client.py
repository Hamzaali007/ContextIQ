from groq import Groq
from config import settings


def get_groq_client(use_fallback: bool = False) -> Groq:
    """Returns a Groq client. Uses fallback API key if primary fails or use_fallback=True."""
    api_key = settings.GROQ_FALLBACK_API_KEY if use_fallback else settings.GROQ_API_KEY
    return Groq(api_key=api_key)


def _extract_content(response) -> str:
    """Safely extract text content from a Groq completion response."""
    content = response.choices[0].message.content
    if content is None:
        raise RuntimeError("Groq returned an empty response (no content).")
    return content


def generate_completion(prompt: str, system_prompt: str = "", temperature: float = 0.3) -> str:
    """
    Send a prompt to Groq and return the text response.
    Automatically retries with fallback key if the primary key fails.
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        client = get_groq_client(use_fallback=False)
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=messages,
            temperature=temperature,
        )
        return _extract_content(response)

    except Exception as primary_error:
        if not settings.GROQ_FALLBACK_API_KEY:
            raise primary_error

        try:
            client = get_groq_client(use_fallback=True)
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=messages,
                temperature=temperature,
            )
            return _extract_content(response)
        except Exception as fallback_error:
            raise RuntimeError(
                f"Both Groq API keys failed. Primary: {primary_error}. Fallback: {fallback_error}"
            )


def generate_completion_stream(prompt:str,system_prompt:str="",temperature:float = 0.3):
    """
    Yields text chunks as they arrive from Groq.Note:fallback-key retry works if the connection fails before the first chunks streams(cant restarta generator mid stream) accpetable tradeooff for the speed gain

    """
    messages = []
    if system_prompt:
        messages.append({"role":"system","content":system_prompt})
    messages.append({"role":"user","content":prompt})

    def _stream_with(client):
        stream = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages = messages,
            temperature = temperature,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    try:
        client = get_groq_client(use_fallback=False)
        yield from _stream_with(client)
    except Exception as primary_error:
        if not settings.GROQ_FALLBACK_API_KEY:
            raise  primary_error

        client = get_groq_client(use_fallback=True)
        yield from _stream_with(client)


