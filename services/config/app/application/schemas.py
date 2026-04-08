"""
Pydantic schemas for API requests/responses.
"""

from pydantic import BaseModel, Field
from typing import Any, Optional, Dict, List


class ConfigResponseSchema(BaseModel):
    """Response schema for single configuration"""
    
    key: str
    value: Any
    config_type: str
    description: str
    category: str
    editable: bool
    required: bool
    default_value: Optional[Any] = None
    
    class Config:
        from_attributes = True


class CategoryConfigResponseSchema(BaseModel):
    """Response schema for category configurations"""
    
    category: str
    parameters: Dict[str, Dict[str, Any]]


class AllConfigResponseSchema(BaseModel):
    """Response schema for all configurations"""
    
    configurations: Dict[str, Dict[str, Dict[str, Any]]]


class UpdateConfigRequestSchema(BaseModel):
    """Request schema for updating single configuration"""
    
    value: Any = Field(..., description="New configuration value")
    reason: Optional[str] = Field(None, description="Reason for change")


class BulkUpdateConfigRequestSchema(BaseModel):
    """Request schema for bulk updating configurations"""
    
    updates: Dict[str, Any] = Field(..., description="Dictionary of key-value updates")
    reason: Optional[str] = Field(None, description="Reason for bulk change")


class AuditLogResponseSchema(BaseModel):
    """Response schema for audit log entry"""
    
    id: int
    config_key: str
    old_value: Optional[Any]
    new_value: Any
    changed_by: str
    change_reason: Optional[str]
    changed_at: str


class AuditLogListResponseSchema(BaseModel):
    """Response schema for audit log list"""
    
    logs: List[AuditLogResponseSchema]
    total: int


class ErrorResponseSchema(BaseModel):
    """Response schema for errors"""
    
    error: str
    detail: Optional[str] = None
    timestamp: str
