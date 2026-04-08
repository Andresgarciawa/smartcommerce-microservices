"""
Application layer - Use cases for configuration management.
"""

from typing import Optional, List, Dict, Any
from app.domain.models import ConfigParam, ConfigType
from app.infrastructure.repository import ConfigurationRepository
from app.domain.default_config import DEFAULT_CONFIG
import json


class InitializeConfigurationUseCase:
    """Initialize system with default configuration"""
    
    def __init__(self, repository: ConfigurationRepository):
        self.repository = repository
    
    def execute(self, admin_id: str = "system"):
        """Load default configuration into database"""
        for category, params in DEFAULT_CONFIG.items():
            for key, value in params.items():
                full_key = f"{category}.{key}"
                
                # Check if already exists
                existing = self.repository.get_by_key(full_key)
                if existing:
                    continue
                
                # Determine type
                if isinstance(value, bool):
                    config_type = ConfigType.BOOLEAN
                elif isinstance(value, int):
                    config_type = ConfigType.INTEGER
                elif isinstance(value, float):
                    config_type = ConfigType.FLOAT
                elif isinstance(value, list):
                    config_type = ConfigType.ARRAY
                elif isinstance(value, dict):
                    config_type = ConfigType.JSON
                else:
                    config_type = ConfigType.STRING
                
                config = ConfigParam(
                    key=full_key,
                    value=value,
                    description=self._get_description(category, key),
                    config_type=config_type,
                    category=category,
                    required=False,
                    editable=True,
                    default_value=value
                )
                
                config.validate()
                self.repository.create(config, admin_id)
    
    def _get_description(self, category: str, key: str) -> str:
        """Get description for configuration parameter"""
        from app.domain.default_config import CONFIG_METADATA
        
        return CONFIG_METADATA.get(category, {}).get(key, f"Configuration: {category}.{key}")


class GetConfigurationUseCase:
    """Get configuration parameter"""
    
    def __init__(self, repository: ConfigurationRepository):
        self.repository = repository
    
    def get_by_key(self, key: str) -> Optional[ConfigParam]:
        """Get single configuration by key"""
        return self.repository.get_by_key(key)
    
    def get_category(self, category: str) -> Dict[str, Any]:
        """Get all configurations in a category"""
        configs = self.repository.get_all_by_category(category)
        
        result = {}
        for config in configs:
            # Remove category prefix from key for cleaner output
            clean_key = config.key.replace(f"{category}.", "")
            result[clean_key] = {
                "value": config.value,
                "type": config.config_type.value,
                "description": config.description,
                "editable": config.editable,
                "required": config.required
            }
        
        return result
    
    def get_all(self) -> Dict[str, Dict[str, Any]]:
        """Get all configurations grouped by category"""
        configs = self.repository.get_all()
        
        result = {}
        for config in configs:
            if config.category not in result:
                result[config.category] = {}
            
            # Remove category prefix from key
            clean_key = config.key.replace(f"{config.category}.", "")
            result[config.category][clean_key] = {
                "value": config.value,
                "type": config.config_type.value,
                "description": config.description,
                "editable": config.editable,
                "required": config.required,
                "full_key": config.key
            }
        
        return result


class UpdateConfigurationUseCase:
    """Update configuration parameter"""
    
    def __init__(self, repository: ConfigurationRepository):
        self.repository = repository
    
    def update_single(self, key: str, new_value: Any, user_id: str, reason: Optional[str] = None) -> Optional[ConfigParam]:
        """Update single configuration"""
        config = self.repository.get_by_key(key)
        
        if not config:
            raise ValueError(f"Configuration '{key}' not found")
        
        if not config.editable:
            raise ValueError(f"Configuration '{key}' is not editable")
        
        # Validate new value
        test_config = ConfigParam(
            key=config.key,
            value=new_value,
            description=config.description,
            config_type=config.config_type,
            category=config.category,
            required=config.required,
            editable=config.editable,
            default_value=config.default_value
        )
        test_config.validate()
        
        return self.repository.update(key, new_value, user_id, reason)
    
    def update_multiple(self, updates: Dict[str, Any], user_id: str, reason: Optional[str] = None) -> Dict[str, ConfigParam]:
        """Update multiple configurations"""
        results = {}
        
        for key, new_value in updates.items():
            config = self.repository.get_by_key(key)
            
            if not config:
                raise ValueError(f"Configuration '{key}' not found")
            
            if not config.editable:
                raise ValueError(f"Configuration '{key}' is not editable")
            
            # Validate
            test_config = ConfigParam(
                key=config.key,
                value=new_value,
                description=config.description,
                config_type=config.config_type,
                category=config.category,
                required=config.required,
                editable=config.editable,
                default_value=config.default_value
            )
            test_config.validate()
            
            results[key] = config
        
        # All validations passed, perform updates
        self.repository.bulk_update(updates, user_id, reason)
        
        return {key: self.repository.get_by_key(key) for key in updates.keys()}


class GetAuditLogUseCase:
    """Get configuration audit log"""
    
    def __init__(self, repository: ConfigurationRepository):
        self.repository = repository
    
    def execute(self, config_key: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get audit log"""
        return self.repository.get_audit_log(config_key, limit)
