from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from .database import Base
import datetime


class EnrichmentRequestORM(Base):
    __tablename__ = "enrichment_requests"

    id = Column(String, primary_key=True, index=True)  # UUID
    book_reference = Column(String, nullable=False, index=True)
    requested_at = Column(DateTime, default=datetime.datetime.utcnow)
    source_used = Column(String)
    status = Column(String, nullable=False, default="pending")


class EnrichmentResultORM(Base):
    __tablename__ = "enrichment_results"

    id = Column(String, primary_key=True, index=True)  # UUID
    request_id = Column(String, ForeignKey("enrichment_requests.id"), nullable=False)
    normalized_title = Column(String)
    normalized_author = Column(String)
    normalized_publisher = Column(String)
    normalized_description = Column(Text)
    cover_url = Column(String)
    metadata_json = Column(JSON)
