"""
API routes for configuration management.
FastAPI routers for HTTP endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Dict, Any

from app.infrastructure.database import get_db
from app.infrastructure.repository import ConfigurationRepository
from app.application.use_cases import (
    GetConfigurationUseCase,
    UpdateConfigurationUseCase,
    GetAuditLogUseCase,
    InitializeConfigurationUseCase
)
from app.application.schemas import (
    ConfigResponseSchema,
    UpdateConfigRequestSchema,
    BulkUpdateConfigRequestSchema,
    AuditLogListResponseSchema,
    AuditLogResponseSchema,
    ErrorResponseSchema,
    AllConfigResponseSchema,
    CategoryConfigResponseSchema
)

router = APIRouter(prefix="/config", tags=["configuration"])


def get_user_id(authorization: Optional[str] = Header(None)) -> str:
    """Extract user ID from token header"""
    # TODO: Implement proper JWT validation
    # For now, use a simple extraction or default
    if authorization and authorization.startswith("Bearer "):
        # In production, decode JWT and extract user ID
        return authorization.split(" ")[1][:10]  # Temporary
    return "system"


@router.post("/initialize", response_model=Dict[str, str], tags=["admin"])
def initialize_config(db: Session = Depends(get_db)):
    """
    Initialize system with default configuration.
    Only call once during system setup.
    """
    try:
        repository = ConfigurationRepository(db)
        use_case = InitializeConfigurationUseCase(repository)
        use_case.execute()
        
        return {
            "message": "Configuration initialized successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "config",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/", response_model=AllConfigResponseSchema)
def get_all_config(db: Session = Depends(get_db)):
    """
    Get all system configurations grouped by category.
    """
    try:
        repository = ConfigurationRepository(db)
        use_case = GetConfigurationUseCase(repository)
        configs = use_case.get_all()
        
        return AllConfigResponseSchema(configurations=configs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{category}", response_model=CategoryConfigResponseSchema)
def get_category_config(
    category: str,
    db: Session = Depends(get_db)
):
    """
    Get all configurations in a specific category.
    
    Categories: pricing, inventory, enrichment, system, api
    """
    try:
        repository = ConfigurationRepository(db)
        use_case = GetConfigurationUseCase(repository)
        params = use_case.get_category(category)
        
        if not params:
            raise HTTPException(
                status_code=404,
                detail=f"Category '{category}' not found or has no configurations"
            )
        
        return CategoryConfigResponseSchema(
            category=category,
            parameters=params
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{category}/{key}", response_model=ConfigResponseSchema)
def get_single_config(
    category: str,
    key: str,
    db: Session = Depends(get_db)
):
    """
    Get a single configuration parameter.
    
    The key is the parameter name without the category prefix.
    """
    try:
        full_key = f"{category}.{key}"
        
        repository = ConfigurationRepository(db)
        use_case = GetConfigurationUseCase(repository)
        config = use_case.get_by_key(full_key)
        
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Configuration '{full_key}' not found"
            )
        
        return ConfigResponseSchema(
            key=config.key,
            value=config.value,
            config_type=config.config_type.value,
            description=config.description,
            category=config.category,
            editable=config.editable,
            required=config.required,
            default_value=config.default_value
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{category}/{key}", response_model=ConfigResponseSchema, tags=["admin"])
def update_single_config(
    category: str,
    key: str,
    request: UpdateConfigRequestSchema,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id)
):
    """
    Update a single configuration parameter.
    Requires admin authorization.
    """
    try:
        full_key = f"{category}.{key}"
        
        repository = ConfigurationRepository(db)
        use_case = UpdateConfigurationUseCase(repository)
        
        updated_config = use_case.update_single(
            full_key,
            request.value,
            user_id,
            request.reason
        )
        
        if not updated_config:
            raise HTTPException(status_code=404, detail="Configuration not found")
        
        return ConfigResponseSchema(
            key=updated_config.key,
            value=updated_config.value,
            config_type=updated_config.config_type.value,
            description=updated_config.description,
            category=updated_config.category,
            editable=updated_config.editable,
            required=updated_config.required,
            default_value=updated_config.default_value
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/", response_model=Dict[str, Any], tags=["admin"])
def bulk_update_config(
    request: BulkUpdateConfigRequestSchema,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id)
):
    """
    Update multiple configuration parameters at once.
    Requires admin authorization.
    """
    try:
        repository = ConfigurationRepository(db)
        use_case = UpdateConfigurationUseCase(repository)
        
        updated_configs = use_case.update_multiple(
            request.updates,
            user_id,
            request.reason
        )
        
        return {
            "message": "Configurations updated successfully",
            "updated_count": len(updated_configs),
            "timestamp": datetime.utcnow().isoformat(),
            "keys": list(updated_configs.keys())
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{category}/{key}/audit", response_model=AuditLogListResponseSchema)
def get_config_audit_log(
    category: str,
    key: str,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get audit log for a specific configuration.
    """
    try:
        full_key = f"{category}.{key}"
        
        repository = ConfigurationRepository(db)
        use_case = GetAuditLogUseCase(repository)
        logs = use_case.execute(full_key, limit)
        
        return AuditLogListResponseSchema(
            logs=[AuditLogResponseSchema(**log) for log in logs],
            total=len(logs)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
