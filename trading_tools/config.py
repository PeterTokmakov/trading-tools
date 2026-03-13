#!/usr/bin/env python3
# hash: 2f9a1b

"""
Config module for trading tools.
Provides unified configuration loading for all trading tools.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """Unified configuration manager for trading tools."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize config manager.
        
        Args:
            config_path: Path to config JSON file
        """
        self.config_path = config_path
        self._config = None
    
    def load(self) -> Dict[str, Any]:
        """
        Load configuration from JSON file.
        
        Returns:
            Configuration dictionary
        """
        if not self.config_path:
            raise ValueError("Config path not provided")
        
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = json.load(f)
        
        return self._config
    
    def save(self, config: Dict[str, Any]) -> None:
        """
        Save configuration to JSON file.
        
        Args:
            config: Configuration dictionary to save
        """
        if not self.config_path:
            raise ValueError("Config path not provided")
        
        # Create parent directory if needed
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        self._config = config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'ssh.username')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        if not self._config:
            self.load()
        
        # Support dot notation
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        if not self._config:
            self.load()
        
        # Support dot notation
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get full configuration dictionary."""
        if not self._config:
            self.load()
        return self._config
    
    @config.setter
    def config(self, value: Dict[str, Any]) -> None:
        """Set full configuration dictionary."""
        self._config = value


def load_config(config_path: Path) -> Config:
    """
    Load configuration from file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Config instance
    """
    return Config(config_path)
