"""
Application settings and configuration.
"""

from typing import List, Optional
import os

class Settings:
    """Application settings."""
    
    # API Configuration
    api_title: str = "Government AI Platform API"
    api_version: str = "2.0.0"
    api_description: str = "Sistema de IA para procesamiento de documentos gubernamentales"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # CORS Configuration
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://ai.minedu.gob.pe"
    ]
    
    # Database Configuration
    redis_url: Optional[str] = "redis://localhost:6379"
    
    # AI Model Configuration
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None
    
    # Security Configuration
    secret_key: str = "your-secret-key-change-in-production"
    jwt_secret: str = "your-jwt-secret-change-in-production"
    access_token_expire_minutes: int = 30
    
    # File Upload Configuration
    max_file_size_mb: int = 50
    allowed_file_types: List[str] = [
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/jpg",
        "audio/mpeg",
        "audio/wav"
    ]
    
    # Plugin Configuration
    plugins_config_path: str = "../config/plugins.yaml"
    models_config_path: str = "../config/models.yaml"
    admin_config_path: str = "../config/admin.yaml"
    
    # Monitoring Configuration
    enable_metrics: bool = True
    metrics_port: int = 9090
    log_level: str = "INFO"
    
    # Rate Limiting Configuration
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst: int = 100

# Global settings instance
_settings = None

def get_settings() -> Settings:
    """Get application settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings