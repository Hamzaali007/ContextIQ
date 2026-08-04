
def _limit_content(chunks: list[dict], max_chars: int = 20000) -> tuple[str, bool]:
    """
    Joins chunk text up to a character budget so large page ranges don't
    blow past Groq's TPM rate limit. Returns (content, was_truncated).
    """
    parts = []
    total = 0
    truncated = False
    for c in chunks:
        piece = f"[Page {c.get('page')}]\n{c.get('text', '')}"
        if total + len(piece) > max_chars:
            truncated = True
            break
        parts.append(piece)
        total += len(piece)
    return "\n\n".join(parts), truncated