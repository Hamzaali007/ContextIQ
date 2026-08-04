import uuid
import time
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    PayloadSchemaType,
    Range,
)

from config import settings
from ingestion.embedder import embed_texts, embed_query

EMBEDDING_DIM = 768


def get_client() -> QdrantClient:
    url = settings.QDRANT_URL
    if url:
        url = url.strip().strip("'").strip('"')
    return QdrantClient(
        url=url,
        api_key=settings.QDRANT_API_KEY,
    )


def _retry_on_network_error(func, max_retries: int = 3, delay: float = 1.0):
    """Retries operations if a transient network or DNS resolution error occurs."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            err_str = str(e).lower()
            if (
                "getaddrinfo" in err_str
                or "connection" in err_str
                or "timeout" in err_str
                or "handlingexception" in err_str
            ) and attempt < max_retries - 1:
                time.sleep(delay * (attempt + 1))
                continue
            raise


def create_collection_if_not_exists():
    def _execute():
        client = get_client()
        if not client.collection_exists(settings.QDRANT_COLLECTION):
            client.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
            )
            # Create an index on "source" so we can filter by it later
            client.create_payload_index(
                collection_name=settings.QDRANT_COLLECTION,
                field_name="source",
                field_schema=PayloadSchemaType.KEYWORD,
            )
            # Create an index on "session_id" for per-user isolation
            client.create_payload_index(
                collection_name=settings.QDRANT_COLLECTION,
                field_name="session_id",
                field_schema=PayloadSchemaType.KEYWORD,
            )

    _retry_on_network_error(_execute)


def upsert_chunks(chunks: list[dict], source: str, on_progress=None, session_id: str | None = None) -> int:
    """
    chunks: list of {"page": int, "chunk_id": int, "text": str}
    source: filename/identifier of the PDF, stored in payload for scoped retrieval
    on_progress: optional callable(done: int, total: int, status: str | None),
    forwarded to embed_texts() so a caller can drive a progress bar.
    session_id: browser session UUID — used to isolate each user's uploads.
    """
    create_collection_if_not_exists()

    texts = [c["text"] for c in chunks]
    vectors = embed_texts(texts, on_progress=on_progress)

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vectors[i],
            payload={
                "text": chunks[i]["text"],
                "page": chunks[i]["page"],
                "chunk_id": chunks[i]["chunk_id"],
                "source": source,
                "session_id": session_id or "",
            },
        )
        for i in range(len(chunks))
    ]

    def _execute():
        client = get_client()
        client.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)

    _retry_on_network_error(_execute)
    return len(points)


def search(query: str, source: str | None = None, top_k: int = 5, session_id: str | None = None):
    query_vector = embed_query(query)

    conditions = []
    if source:
        conditions.append(FieldCondition(key="source", match=MatchValue(value=source)))
    if session_id:
        conditions.append(FieldCondition(key="session_id", match=MatchValue(value=session_id)))

    query_filter = Filter(must=conditions) if conditions else None

    def _execute():
        client = get_client()
        if not client.collection_exists(settings.QDRANT_COLLECTION):
            return []
        return client.query_points(
            collection_name=settings.QDRANT_COLLECTION,
            query=query_vector,
            query_filter=query_filter,
            limit=top_k,
        ).points

    try:
        results = _retry_on_network_error(_execute)
    except Exception as e:
        print(f"Warning: Qdrant search failed: {e}")
        return []

    output = []
    for r in results:
        payload = r.payload or {}
        output.append({
            "text": payload.get("text", ""),
            "page": payload.get("page"),
            "source": payload.get("source"),
            "score": r.score,
        })
    return output


def get_max_page(source: str) -> int:
    """
    Return the highest page number stored for this source. Used to correctly
    size page-range sliders (quiz/test/definitions/flashcards) when a document
    was ingested in a *previous* session — st.session_state.total_pages only
    knows about PDFs embedded in the current session, so without this the UI
    silently fell back to a hardcoded default of 50 pages.
    """
    query_filter = Filter(
        must=[FieldCondition(key="source", match=MatchValue(value=source))]
    )

    def _execute():
        client = get_client()
        if not client.collection_exists(settings.QDRANT_COLLECTION):
            return 0
        points, _ = client.scroll(
            collection_name=settings.QDRANT_COLLECTION,
            scroll_filter=query_filter,
            limit=10000,
            with_payload=["page"],
        )
        pages = [p.payload.get("page", 0) for p in points if p.payload]
        return max(pages) if pages else 0

    try:
        return _retry_on_network_error(_execute)
    except Exception as e:
        print(f"Warning: Failed to get max page for source '{source}': {e}")
        return 0


def list_sources(session_id: str | None = None) -> list[str]:
    """Return distinct textbook sources currently stored (for UI dropdown/history).
    When session_id is provided, only return sources belonging to that session."""
    def _execute():
        client = get_client()
        if not client.collection_exists(settings.QDRANT_COLLECTION):
            return []

        scroll_filter = None
        if session_id:
            scroll_filter = Filter(
                must=[FieldCondition(key="session_id", match=MatchValue(value=session_id))]
            )

        all_points, _ = client.scroll(
            collection_name=settings.QDRANT_COLLECTION,
            scroll_filter=scroll_filter,
            limit=10000,
            with_payload=["source"],
        )
        return sorted(set(p.payload["source"] for p in all_points if p.payload and "source" in p.payload))

    try:
        return _retry_on_network_error(_execute)
    except Exception as e:
        print(f"Warning: Failed to list sources from Qdrant: {e}")
        return []


def delete_source(source: str, session_id: str | None = None):
    """Delete all chunks belonging to one textbook (not the whole collection).
    When session_id is provided, only deletes chunks matching both source AND session."""
    def _execute():
        client = get_client()
        if client.collection_exists(settings.QDRANT_COLLECTION):
            conditions = [FieldCondition(key="source", match=MatchValue(value=source))]
            if session_id:
                conditions.append(FieldCondition(key="session_id", match=MatchValue(value=session_id)))
            client.delete(
                collection_name=settings.QDRANT_COLLECTION,
                points_selector=Filter(must=conditions),
            )

    try:
        _retry_on_network_error(_execute)
    except Exception as e:
        print(f"Warning: Failed to delete source from Qdrant: {e}")


def search_by_page_range(source: str, start_page: int, end_page: int, limit: int = 1000, session_id: str | None = None):
    """
    Retrieve all chunks for 'source' within [start_page, end_page] inclusive.
    Used for chapter/range-based quiz generation — structural filtering.
    """
    conditions = [
        FieldCondition(key="source", match=MatchValue(value=source)),
        FieldCondition(key="page", range=Range(gte=start_page, lte=end_page)),
    ]
    if session_id:
        conditions.append(FieldCondition(key="session_id", match=MatchValue(value=session_id)))

    query_filter = Filter(must=conditions)

    def _execute():
        client = get_client()
        if not client.collection_exists(settings.QDRANT_COLLECTION):
            return []
        results, _ = client.scroll(
            collection_name=settings.QDRANT_COLLECTION,
            scroll_filter=query_filter,
            limit=limit,
            with_payload=True,
        )
        return results

    try:
        results = _retry_on_network_error(_execute)
    except Exception as e:
        print(f"Warning: Qdrant page range search failed: {e}")
        return []

    chunks = []
    for r in results:
        payload = r.payload or {}
        chunks.append({
            "text": payload.get("text", ""),
            "page": payload.get("page"),
            "chunk_id": payload.get("chunk_id"),
        })

    chunks.sort(key=lambda c: (c["page"] or 0, c["chunk_id"] or 0))
    return chunks