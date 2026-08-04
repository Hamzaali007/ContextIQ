import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vectorstore.qdrantclient import get_client
from qdrant_client.models import PayloadSchemaType
from config import settings

client = get_client()

try:
    client.create_payload_index(
        collection_name=settings.QDRANT_COLLECTION,
        field_name="source",
        field_schema=PayloadSchemaType.KEYWORD,
    )
    print("Source index created")
except Exception as e:
    print(f"Source index skipped: {e}")

try:
    client.create_payload_index(
        collection_name=settings.QDRANT_COLLECTION,
        field_name="page",
        field_schema=PayloadSchemaType.INTEGER,
    )
    print("Page index created")
except Exception as e:
    print(f"Page index skipped: {e}")