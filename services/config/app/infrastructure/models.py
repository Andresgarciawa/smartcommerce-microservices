"""
Database models for Configuration Service.
SQLAlchemy ORM models for persistence.
"""

from sqlalchemy import Column, String, Text, TIMESTAMP, JSON, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import json

Base = declarative_base()


class ConfigurationDB(Base):
    """Database model for configuration parameters"""
    
    __tablename__ = "configurations"
    
    key = Column(String(255), primary_key=True, nullable=False)
    value = Column(JSON, nullable=False)
    config_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, index=True)
    required = Column(Boolean, default=False)
    editable = Column(Boolean, default=True)
    default_value = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = Column(String(255), nullable=True)  # Admin user ID
    
    def __repr__(self):
        return f"<ConfigurationDB(key={self.key}, category={self.category})>"


class AuditLogDB(Base):
    """Database model for configuration change audit trail"""
    
    __tablename__ = "configuration_audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(255), nullable=False, index=True)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=False)
    changed_by = Column(String(255), nullable=False)
    change_reason = Column(Text, nullable=True)
    changed_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<AuditLogDB(config={self.config_key}, changed_at={self.changed_at})>"
