from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Integer
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
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    isbn = Column(String, index=True)
    request_id = Column(String, ForeignKey("enrichment_requests.id"), nullable=True) # Lo hacemos opcional por ahora
    source = Column(String)
    metadata_json = Column(JSON) # Cambiado a JSON para mejor manejo en Postgres
    
    # Columnas para los datos limpios
    normalized_title = Column(String)
    normalized_author = Column(String)
    normalized_publisher = Column(String)
    normalized_year = Column(Integer)
    normalized_description = Column(Text) # Nombre corregido para consistencia
    cover_url = Column(String)