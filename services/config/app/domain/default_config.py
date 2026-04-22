"""
Default system configuration parameters.
These are initial values that can be overridden.
"""

from typing import Dict, Any

DEFAULT_CONFIG: Dict[str, Dict[str, Any]] = {
    "pricing": {
        "condition_factors": {
            "NUEVO": 1.0,
            "USADO_EXCELENTE": 0.85,
            "USADO_BUENO": 0.70,
            "USADO_ACEPTABLE": 0.50,
            "DAÑADO": 0.30
        },
        "reference_sources": ["GOOGLE_BOOKS", "OPEN_LIBRARY", "CROSSREF"],
        "fallback_margin": 0.15,
        "outlier_threshold": 2.5,
        "min_price": 100,
        "max_price": 500000
    },
    "inventory": {
        "max_file_size": 52428800,  # 50MB
        "allowed_formats": ["xlsx", "xls", "csv"],
        "batch_error_threshold": 10,  # percentage
        "required_fields": ["title", "author", "quantity"],
        "isbn_validation": False,
        "condition_required_for_used": True,
        "max_quantity_per_item": 1000,
        "enrichment_batch_size": 50
    },
    "enrichment": {
        "priority_sources": ["GOOGLE_BOOKS", "CROSSREF", "OPEN_LIBRARY"],
        "batch_size": 50,
        "retry_attempts": 3,
        "timeout_ms": 30000,
        "enabled": True,
        "cache_ttl": 604800  # 7 days in seconds
    },
    "system": {
        "jwt_algorithm": "HS256",
        "jwt_expiration_hours": 24,
        "external_api_timeout": 30000,
        "cache_ttl": 3600,
        "db_pool_size": 20,
        "log_level": "INFO",
        "environment": "development"
    },
    "api": {
        "google_books_enabled": True,
        "crossref_enabled": True,
        "open_library_enabled": True,
        "ebay_enabled": False,
        "retry_on_failure": True
    }
}

# Configuration metadata with descriptions
CONFIG_METADATA: Dict[str, Dict[str, str]] = {
    "pricing": {
        "fallback_margin": "Margin to apply when external APIs fail (0.15 = 15%)",
        "condition_factors": "Price multipliers based on book condition",
        "reference_sources": "Priority order of external price references",
        "outlier_threshold": "Standard deviation threshold for price outliers",
        "min_price": "Minimum allowed selling price (in local currency)",
        "max_price": "Maximum allowed selling price (in local currency)"
    },
    "inventory": {
        "max_file_size": "Maximum upload file size in bytes",
        "allowed_formats": "Supported import file formats",
        "batch_error_threshold": "Maximum error percentage before batch rejection",
        "required_fields": "Fields that must be present in every record",
        "isbn_validation": "Whether to enforce ISBN format validation",
        "condition_required_for_used": "Whether condition field is required for used books"
    },
    "enrichment": {
        "priority_sources": "Order of API sources to query for metadata",
        "batch_size": "Number of records to process in each batch",
        "retry_attempts": "Number of times to retry failed API calls",
        "timeout_ms": "Timeout for API calls in milliseconds"
    },
    "system": {
        "jwt_algorithm": "Algorithm for JWT token signing",
        "jwt_expiration_hours": "JWT token expiration time in hours",
        "external_api_timeout": "General timeout for external APIs in milliseconds"
    }
}
