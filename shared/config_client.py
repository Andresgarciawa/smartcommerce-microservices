"""
Python client library for Configuration Service.
Allows other microservices to fetch and consume configurations.
"""

import requests
from typing import Any, Optional, Dict
from functools import lru_cache
import time
import os


class ConfigClient:
    """Client for Configuration Service"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8008",
        timeout: int = 5,
        cache_ttl: int = 3600
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self._cache = {}
        self._cache_time = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get single configuration value.
        
        Example:
            fallback_margin = client.get("pricing.fallback_margin", default=0.15)
        """
        try:
            parts = key.split('.')
            if len(parts) != 2:
                raise ValueError(f"Invalid key format: {key}. Use 'category.parameter'")
            
            category, param = parts
            return self._get_single(category, param, default)
        except Exception as e:
            if default is not None:
                return default
            raise
    
    def get_category(self, category: str) -> Dict[str, Any]:
        """
        Get all configurations in a category.
        
        Example:
            pricing_config = client.get_category("pricing")
            margin = pricing_config["fallback_margin"]["value"]
        """
        cache_key = f"category:{category}"
        
        # Check cache
        if self._is_cached(cache_key):
            return self._cache[cache_key]
        
        try:
            response = requests.get(
                f"{self.base_url}/config/{category}",
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            # Cache the result
            self._cache[cache_key] = data["parameters"]
            self._cache_time[cache_key] = time.time()
            
            return data["parameters"]
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch category '{category}': {str(e)}")
    
    def get_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all configurations.
        
        Example:
            all_configs = client.get_all()
            pricing = all_configs["pricing"]
        """
        cache_key = "all:configs"
        
        # Check cache
        if self._is_cached(cache_key):
            return self._cache[cache_key]
        
        try:
            response = requests.get(
                f"{self.base_url}/config/",
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            # Cache the result
            self._cache[cache_key] = data["configurations"]
            self._cache_time[cache_key] = time.time()
            
            return data["configurations"]
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch all configurations: {str(e)}")
    
    def clear_cache(self, key: Optional[str] = None):
        """Clear cache entry or all cache"""
        if key:
            self._cache.pop(key, None)
            self._cache_time.pop(key, None)
        else:
            self._cache.clear()
            self._cache_time.clear()
    
    def health_check(self) -> bool:
        """Check if config service is healthy"""
        try:
            response = requests.get(
                f"{self.base_url}/config/health",
                timeout=self.timeout
            )
            return response.status_code == 200
        except:
            return False
    
    # Private methods
    
    def _get_single(self, category: str, param: str, default: Any) -> Any:
        """Get single configuration with cache"""
        cache_key = f"{category}:{param}"
        
        # Check cache
        if self._is_cached(cache_key):
            return self._cache[cache_key]
        
        try:
            response = requests.get(
                f"{self.base_url}/config/{category}/{param}",
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            value = data["value"]
            
            # Cache the result
            self._cache[cache_key] = value
            self._cache_time[cache_key] = time.time()
            
            return value
        except requests.RequestException as e:
            if default is not None:
                return default
            raise Exception(f"Failed to fetch configuration '{category}.{param}': {str(e)}")
    
    def _is_cached(self, key: str) -> bool:
        """Check if cache entry is valid"""
        if key not in self._cache:
            return False
        
        if key not in self._cache_time:
            return False
        
        # Check if cache expired
        age = time.time() - self._cache_time[key]
        return age < self.cache_ttl


# Singleton instance
_client = None


def get_client(base_url: Optional[str] = None) -> ConfigClient:
    """Get or create singleton config client"""
    global _client
    
    if _client is None:
        url = base_url or os.getenv(
            "CONFIG_SERVICE_URL",
            "http://localhost:8008"
        )
        _client = ConfigClient(base_url=url)
    
    return _client


# Usage examples
if __name__ == "__main__":
    client = ConfigClient(base_url="http://localhost:8008")
    
    # Get single value
    print(client.get("pricing.fallback_margin", default=0.15))
    
    # Get category
    pricing = client.get_category("pricing")
    print(pricing)
    
    # Get all
    all_config = client.get_all()
    print(all_config)
