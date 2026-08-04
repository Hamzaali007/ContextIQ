
import time
import random
from typing import List, Optional, Callable
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config import settings

# --- Configuration ---
EMBED_BATCH_SIZE = 100
BATCH_PAUSE_SECONDS = 60
MAX_RETRIES_PER_KEY = 5
RETRY_BACKOFF_BASE = 2

# Parse multiple API keys from settings (comma-separated)
# If only one key, it works as before.
_api_keys = getattr(settings, "GEMINI_API_KEYS", None)
if isinstance(_api_keys, str):
    API_KEYS = [k.strip() for k in _api_keys.split(",") if k.strip()]
else:
    API_KEYS = [settings.GEMINI_API_KEY]  # fallback to single key

if not API_KEYS:
    raise ValueError("No Gemini API keys found in settings.")


def get_embeddings_function(api_key: str):
    """Return a Langchain embedding function for a given API key."""
    return GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-2-preview",
        api_key=api_key,
        output_dimensionality=768,
    )


def _is_rate_limit_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "429" in msg or "resource_exhausted" in msg or "rate limit" in msg


def _is_quota_exceeded_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "quota exceeded" in msg or "daily limit" in msg or "monthly limit" in msg


def embed_texts(
    texts: list[str],
    on_progress: Optional[Callable[[int, int, Optional[str]], None]] = None,
) -> list[list[float]]:
    """
    Embed texts with automatic fallback across multiple Gemini API keys.
    """
    if not texts:
        return []

    total = len(texts)
    all_vectors: list[list[float]] = []

    # wave_start tracks GLOBAL progress across ALL keys. It must live outside
    # the key loop -- if it were reset to 0 per key, a key switch after
    # partial progress would re-embed already-completed chunks, bloating
    # all_vectors past `total` and misaligning vectors[i] with chunks[i]
    # downstream in upsert_chunks().
    wave_start = 0

    # We'll try each key in order; if one fails permanently, move to next,
    # resuming from wherever the previous key left off.
    for key_idx, api_key in enumerate(API_KEYS):
        if wave_start >= total:
            break  # already done, no need to spin up this key

        embedder = get_embeddings_function(api_key)
        key_name = f"Key {key_idx + 1}"
        key_failed = False

        while wave_start < total:
            wave = texts[wave_start:wave_start + EMBED_BATCH_SIZE]
            attempt = 0

            while True:
                try:
                    vectors = embedder.embed_documents(wave)
                    all_vectors.extend(vectors)
                    break  # success for this wave
                except Exception as e:
                    if _is_quota_exceeded_error(e):
                        # Daily quota used up for this key – move to next key,
                        # resuming from the current wave_start (not from 0).
                        if on_progress:
                            on_progress(
                                len(all_vectors), total,
                                f"{key_name} daily quota exhausted. Switching to next API key..."
                            )
                        key_failed = True
                        break
                    elif _is_rate_limit_error(e) and attempt < MAX_RETRIES_PER_KEY:
                        attempt += 1
                        wait_seconds = RETRY_BACKOFF_BASE * (attempt ** 2) + random.uniform(0, 5)
                        if on_progress:
                            on_progress(
                                len(all_vectors), total,
                                f"{key_name} rate limit. Retry {attempt}/{MAX_RETRIES_PER_KEY} in {int(wait_seconds)}s..."
                            )
                        time.sleep(wait_seconds)
                        continue
                    else:
                        # Non-retryable error or retries exhausted – try next key,
                        # resuming from the current wave_start (not from 0).
                        if on_progress:
                            on_progress(
                                len(all_vectors), total,
                                f"{key_name} failed: {str(e)[:50]}. Switching to next key..."
                            )
                        key_failed = True
                        break

            if key_failed:
                break  # go to next key in the outer for-loop

            # Success for this wave – advance global progress
            wave_start += len(wave)

            # Pause between waves (skip the pause if we just finished)
            if wave_start < total:
                time.sleep(BATCH_PAUSE_SECONDS)

            # Progress update after each wave
            if on_progress:
                on_progress(len(all_vectors), total, None)

    # If we've exhausted all keys and still not complete
    if wave_start < total or len(all_vectors) < total:
        raise RuntimeError(
            f"All Gemini API keys exhausted or failed. Only embedded {len(all_vectors)}/{total} chunks. "
            "Please check your keys or try again later."
        )

    return all_vectors


def embed_query(text: str) -> list[float]:
    """Embed a single query using the first available key."""
    for api_key in API_KEYS:
        try:
            embedder = get_embeddings_function(api_key)
            return embedder.embed_query(text)
        except Exception:
            continue
    raise RuntimeError("All Gemini API keys failed for query embedding.")