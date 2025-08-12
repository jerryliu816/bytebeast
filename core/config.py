"""
Configuration management for ByteBeast.
"""

import yaml
from pathlib import Path
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for ByteBeast."""
    
    def __init__(self, config_path: str = None):
        """Initialize configuration."""
        self.config_path = config_path
        self._config = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from YAML files."""
        # Load defaults first
        defaults_path = Path(__file__).parent.parent / "config" / "defaults.yaml"
        if defaults_path.exists():
            with open(defaults_path, 'r') as f:
                self._config = yaml.safe_load(f)
        
        # Override with custom config if provided
        if self.config_path:
            custom_path = Path(self.config_path)
            if custom_path.exists():
                try:
                    with open(custom_path, 'r') as f:
                        custom_config = yaml.safe_load(f)
                        self._deep_merge(self._config, custom_config)
                        logger.info(f"Loaded custom config from {custom_path}")
                except Exception as e:
                    logger.error(f"Error loading custom config: {e}")
    
    def _deep_merge(self, base: Dict, override: Dict):
        """Recursively merge configuration dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation."""
        keys = key.split('.')
        config = self._config
        
        # Navigate to parent of target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section."""
        return self.get(section, {})
    
    def save(self, path: str = None):
        """Save configuration to YAML file."""
        output_path = path or self.config_path
        if output_path:
            with open(output_path, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False)
    
    @property
    def display(self) -> Dict[str, Any]:
        """Get display configuration."""
        return self.get_section('display')
    
    @property 
    def evolution(self) -> Dict[str, Any]:
        """Get evolution configuration."""
        return self.get_section('evolution')
    
    @property
    def thresholds(self) -> Dict[str, Any]:
        """Get threshold configuration."""
        return self.get_section('thresholds')
    
    @property
    def needs(self) -> Dict[str, Any]:
        """Get needs configuration."""
        return self.get_section('needs')
    
    @property
    def sensors(self) -> Dict[str, Any]:
        """Get sensor configuration."""
        return self.get_section('sensors')
    
    @property
    def power(self) -> Dict[str, Any]:
        """Get power configuration."""
        return self.get_section('power')
    
    @property
    def social(self) -> Dict[str, Any]:
        """Get social configuration."""
        return self.get_section('social')
    
    @property
    def mqtt(self) -> Dict[str, Any]:
        """Get MQTT configuration."""
        return self.get_section('mqtt')


# Global configuration instance
_config_instance = None


def get_config(config_path: str = None) -> Config:
    """Get singleton configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance


def reload_config(config_path: str = None):
    """Reload configuration from files."""
    global _config_instance
    _config_instance = Config(config_path)