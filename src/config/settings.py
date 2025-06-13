#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration settings for the MINEDU Document Search System.

This module provides centralized configuration management for all
components of the search system.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import json


class Settings:
    """
    Centralized configuration settings for the search system.
    
    This class manages all configuration parameters including paths,
    model settings, and system parameters.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize settings from config file or defaults.
        
        Args:
            config_file (Optional[str]): Path to configuration file
        """
        self.config_file = config_file
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file or use defaults."""
        if self.config_file and Path(self.config_file).exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration settings."""
        return {
            "paths": {
                "data_dir": "data",
                "processed_dir": "data/processed",
                "vectorstores_dir": "data/vectorstores",
                "logs_dir": "logs",
                "models_dir": "models",
                "chunks_file": "data/processed/chunks.json",
                "vectorstores": {
                    "bm25": "data/vectorstores/bm25.pkl",
                    "tfidf": "data/vectorstores/tfidf.pkl",
                    "transformers": "data/vectorstores/transformers.pkl"
                }
            },
            "models": {
                "transformer_model": "paraphrase-multilingual-MiniLM-L12-v2",
                "fallback_model": "paraphrase-MiniLM-L6-v2",
                "spacy_model": "es_core_news_sm",
                "device": "cpu"
            },
            "search": {
                "default_top_k": 5,
                "fusion_strategy": "weighted",
                "weights": {
                    "bm25": 0.3,
                    "tfidf": 0.3,
                    "transformer": 0.4
                }
            },
            "preprocessing": {
                "chunk_size": 512,
                "chunk_overlap": 50,
                "max_chunks_per_document": 100
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file_logging": True
            }
        }
    
    def get_path(self, key: str) -> str:
        """
        Get a path from configuration.
        
        Args:
            key (str): Path key (e.g., 'data_dir', 'vectorstores.bm25')
            
        Returns:
            str: Resolved path
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                raise KeyError(f"Path key '{key}' not found in configuration")
        
        return str(value)
    
    def get_model_config(self, model_type: str) -> Dict[str, Any]:
        """
        Get model configuration.
        
        Args:
            model_type (str): Type of model ('transformer', 'spacy', etc.)
            
        Returns:
            Dict[str, Any]: Model configuration
        """
        return self.config.get("models", {}).get(model_type, {})
    
    def get_search_config(self) -> Dict[str, Any]:
        """
        Get search configuration.
        
        Returns:
            Dict[str, Any]: Search configuration
        """
        return self.config.get("search", {})
    
    def get_preprocessing_config(self) -> Dict[str, Any]:
        """
        Get preprocessing configuration.
        
        Returns:
            Dict[str, Any]: Preprocessing configuration
        """
        return self.config.get("preprocessing", {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get logging configuration.
        
        Returns:
            Dict[str, Any]: Logging configuration
        """
        return self.config.get("logging", {})
    
    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            self.get_path("data_dir"),
            self.get_path("processed_dir"),
            self.get_path("vectorstores_dir"),
            self.get_path("logs_dir"),
            self.get_path("models_dir")
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def save_config(self, filepath: Optional[str] = None) -> None:
        """
        Save current configuration to file.
        
        Args:
            filepath (Optional[str]): Path to save configuration file
        """
        if filepath is None:
            filepath = self.config_file or "config.json"
        
        with open(filepath, 'w') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        Update configuration with new values.
        
        Args:
            updates (Dict[str, Any]): Configuration updates
        """
        def deep_update(d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
            for k, v in u.items():
                if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                    d[k] = deep_update(d[k], v)
                else:
                    d[k] = v
            return d
        
        self.config = deep_update(self.config, updates)


# Global settings instance
_settings: Optional[Settings] = None


def get_settings(config_file: Optional[str] = None) -> Settings:
    """
    Get global settings instance.
    
    Args:
        config_file (Optional[str]): Path to configuration file
        
    Returns:
        Settings: Global settings instance
    """
    global _settings
    
    if _settings is None:
        _settings = Settings(config_file)
    
    return _settings


def update_settings(updates: Dict[str, Any]) -> None:
    """
    Update global settings.
    
    Args:
        updates (Dict[str, Any]): Configuration updates
    """
    global _settings
    
    if _settings is None:
        _settings = Settings()
    
    _settings.update_config(updates)


# Environment variable overrides
def load_from_env() -> None:
    """Load configuration overrides from environment variables."""
    env_mappings = {
        "MINEDU_DATA_DIR": ("paths", "data_dir"),
        "MINEDU_TRANSFORMER_MODEL": ("models", "transformer_model"),
        "MINEDU_DEVICE": ("models", "device"),
        "MINEDU_DEFAULT_TOP_K": ("search", "default_top_k"),
        "MINEDU_FUSION_STRATEGY": ("search", "fusion_strategy"),
        "MINEDU_LOG_LEVEL": ("logging", "level")
    }
    
    settings = get_settings()
    
    for env_var, config_path in env_mappings.items():
        value = os.getenv(env_var)
        if value is not None:
            keys = config_path.split('.')
            config_section = settings.config
            for key in keys[:-1]:
                config_section = config_section[key]
            config_section[keys[-1]] = value


if __name__ == "__main__":
    # Example usage
    settings = get_settings()
    
    print("Current configuration:")
    print(f"Data directory: {settings.get_path('data_dir')}")
    print(f"Transformer model: {settings.get_model_config('transformer_model')}")
    print(f"Search config: {settings.get_search_config()}")
    
    # Ensure directories exist
    settings.ensure_directories()
    print("Directories created successfully") 