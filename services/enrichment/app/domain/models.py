from pydantic import BaseModel, HttpUrl
from typing import Optional, Any
import datetime


class EnrichmentRequest(BaseModel):
    id: Optional[str] = None
    book_reference: str
    requested_at: Optional[datetime.datetime] = None
    source_used: Optional[str] = None
    status: str = "pending"


class EnrichmentResult(BaseModel):
    id: Optional[str] = None
    request_id: str
    normalized_title: Optional[str] = None
    normalized_author: Optional[str] = None
    normalized_publisher: Optional[str] = None
    normalized_description: Optional[str] = None
    cover_url: Optional[str] = None
    metadata_json: Optional[dict[str, Any]] = None
