"""
Repository pattern for data access.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.infrastructure.models import ConfigurationDB, AuditLogDB
from app.domain.models import ConfigParam, ConfigType
import json


class ConfigurationRepository:
    """Repository for configuration data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_key(self, key: str) -> Optional[ConfigParam]:
        """Get configuration by key"""
        config = self.db.query(ConfigurationDB).filter(
            ConfigurationDB.key == key
        ).first()
        
        if not config:
            return None
        
        return self._to_domain_model(config)
    
    def get_all_by_category(self, category: str) -> List[ConfigParam]:
        """Get all configurations in a category"""
        configs = self.db.query(ConfigurationDB).filter(
            ConfigurationDB.category == category
        ).order_by(ConfigurationDB.key).all()
        
        return [self._to_domain_model(c) for c in configs]
    
    def get_all(self) -> List[ConfigParam]:
        """Get all configurations"""
        configs = self.db.query(ConfigurationDB).order_by(
            ConfigurationDB.category,
            ConfigurationDB.key
        ).all()
        
        return [self._to_domain_model(c) for c in configs]
    
    def create(self, config: ConfigParam, created_by: str) -> ConfigParam:
        """Create new configuration"""
        db_config = ConfigurationDB(
            key=config.key,
            value=config.value,
            config_type=config.config_type.value,
            description=config.description,
            category=config.category,
            required=config.required,
            editable=config.editable,
            default_value=config.default_value,
            updated_by=created_by
        )
        
        self.db.add(db_config)
        self.db.commit()
        self.db.refresh(db_config)
        
        return self._to_domain_model(db_config)
    
    def update(self, key: str, new_value: Any, updated_by: str, reason: Optional[str] = None) -> Optional[ConfigParam]:
        """Update configuration value"""
        config = self.db.query(ConfigurationDB).filter(
            ConfigurationDB.key == key
        ).first()
        
        if not config:
            return None
        
        if not config.editable:
            raise ValueError(f"Configuration '{key}' is not editable")
        
        # Log the change
        self._log_change(key, config.value, new_value, updated_by, reason)
        
        # Update the configuration
        config.value = new_value
        config.updated_by = updated_by
        
        self.db.commit()
        self.db.refresh(config)
        
        return self._to_domain_model(config)
    
    def bulk_update(self, updates: Dict[str, Any], updated_by: str, reason: Optional[str] = None) -> List[ConfigParam]:
        """Update multiple configurations at once"""
        results = []
        
        for key, new_value in updates.items():
            config = self.db.query(ConfigurationDB).filter(
                ConfigurationDB.key == key
            ).first()
            
            if not config:
                continue
            
            if config.editable:
                self._log_change(key, config.value, new_value, updated_by, reason)
                config.value = new_value
                config.updated_by = updated_by
                results.append(self._to_domain_model(config))
        
        self.db.commit()
        return results
    
    def delete(self, key: str, deleted_by: str) -> bool:
        """Delete configuration"""
        config = self.db.query(ConfigurationDB).filter(
            ConfigurationDB.key == key
        ).first()
        
        if not config:
            return False
        
        self._log_change(key, config.value, None, deleted_by, "Configuration deleted")
        self.db.delete(config)
        self.db.commit()
        
        return True
    
    def get_audit_log(self, config_key: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get audit log"""
        query = self.db.query(AuditLogDB)
        
        if config_key:
            query = query.filter(AuditLogDB.config_key == config_key)
        
        logs = query.order_by(desc(AuditLogDB.changed_at)).limit(limit).all()
        
        return [
            {
                "id": log.id,
                "config_key": log.config_key,
                "old_value": log.old_value,
                "new_value": log.new_value,
                "changed_by": log.changed_by,
                "change_reason": log.change_reason,
                "changed_at": log.changed_at.isoformat()
            }
            for log in logs
        ]
    
    def _to_domain_model(self, db_config: ConfigurationDB) -> ConfigParam:
        """Convert database model to domain model"""
        return ConfigParam(
            key=db_config.key,
            value=db_config.value,
            description=db_config.description,
            config_type=ConfigType(db_config.config_type),
            category=db_config.category,
            required=db_config.required,
            editable=db_config.editable,
            default_value=db_config.default_value
        )
    
    def _log_change(self, key: str, old_value: Any, new_value: Any, changed_by: str, reason: Optional[str]):
        """Log configuration change to audit trail"""
        log = AuditLogDB(
            config_key=key,
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by,
            change_reason=reason
        )
        self.db.add(log)
        # Don't commit here - let the caller manage transaction
