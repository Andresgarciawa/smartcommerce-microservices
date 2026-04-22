"""
Domain models for Configuration Service.
Pure business logic, no database dependencies.
"""

from typing import Any, Optional, Dict
from dataclasses import dataclass
from enum import Enum


class ConfigType(str, Enum):
    """Types of configuration parameters"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    ARRAY = "array"


@dataclass
class ConfigParam:
    """Domain model for a configuration parameter"""
    
    key: str
    value: Any
    description: str
    config_type: ConfigType
    category: str
    required: bool = False
    editable: bool = True
    default_value: Optional[Any] = None
    
    def validate(self) -> bool:
        """Validate configuration parameter"""
        if self.required and self.value is None:
            raise ValueError(f"Required parameter '{self.key}' cannot be None")
        
        # Type validation
        if not self._validate_type():
            raise ValueError(f"Invalid type for '{self.key}': expected {self.config_type}")
        
        return True
    
    def _validate_type(self) -> bool:
        """Validate value matches config_type"""
        if self.value is None and not self.required:
            return True
        
        type_mapping = {
            ConfigType.STRING: str,
            ConfigType.INTEGER: int,
            ConfigType.FLOAT: (int, float),
            ConfigType.BOOLEAN: bool,
            ConfigType.JSON: dict,
            ConfigType.ARRAY: list,
        }
        
        expected_type = type_mapping.get(self.config_type)
        return isinstance(self.value, expected_type) if expected_type else True


@dataclass
class ConfigCategory:
    """Domain model for configuration category"""
    
    name: str
    description: str
    order: int = 0


# Known categories
PRICING_CATEGORY = ConfigCategory(
    name="pricing",
    description="Pricing engine configuration",
    order=1
)

INVENTORY_CATEGORY = ConfigCategory(
    name="inventory",
    description="Inventory and import configuration",
    order=2
)

ENRICHMENT_CATEGORY = ConfigCategory(
    name="enrichment",
    description="AI enrichment service configuration",
    order=3
)

SYSTEM_CATEGORY = ConfigCategory(
    name="system",
    description="General system configuration",
    order=4
)

API_CATEGORY = ConfigCategory(
    name="api",
    description="External APIs configuration",
    order=5
)
