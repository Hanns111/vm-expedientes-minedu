#!/usr/bin/env python3
"""
Secure Secrets Management for MINEDU Backend
Supports Docker Secrets, Kubernetes Secrets, and HashiCorp Vault
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
import base64
import hashlib
from functools import lru_cache

logger = logging.getLogger('minedu.secrets')

class SecretsManager:
    """Centralized secrets management with multiple backends"""
    
    def __init__(self, 
                 secrets_path: str = "/run/secrets",
                 vault_url: str = None,
                 vault_token: str = None,
                 encryption_key: str = None):
        
        self.secrets_path = Path(secrets_path)
        self.vault_url = vault_url
        self.vault_token = vault_token
        
        # Initialize encryption
        if encryption_key:
            self.cipher = Fernet(encryption_key.encode()[:32].ljust(32, b'0'))
        else:
            # Generate key from system info (not recommended for production)
            key = hashlib.sha256(os.uname().machine.encode()).digest()
            self.cipher = Fernet(base64.urlsafe_b64encode(key))
        
        logger.info("Secrets manager initialized")
    
    @lru_cache(maxsize=128)
    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret from available backends (cached)"""
        
        # 1. Try Docker Secrets first (production)
        docker_secret = self._get_docker_secret(secret_name)
        if docker_secret:
            return docker_secret
        
        # 2. Try Kubernetes Secrets
        k8s_secret = self._get_k8s_secret(secret_name)
        if k8s_secret:
            return k8s_secret
        
        # 3. Try HashiCorp Vault
        vault_secret = self._get_vault_secret(secret_name)
        if vault_secret:
            return vault_secret
        
        # 4. Try environment variables (development)
        env_secret = os.getenv(secret_name.upper())
        if env_secret:
            logger.warning(f"Using environment variable for {secret_name} (not recommended for production)")
            return env_secret
        
        # 5. Return default
        if default is not None:
            logger.warning(f"Using default value for secret {secret_name}")
            return default
        
        logger.error(f"Secret not found: {secret_name}")
        return None
    
    def _get_docker_secret(self, secret_name: str) -> Optional[str]:
        """Read secret from Docker Secrets mount point"""
        try:
            secret_file = self.secrets_path / secret_name
            if secret_file.exists():
                content = secret_file.read_text().strip()
                logger.debug(f"Loaded Docker secret: {secret_name}")
                return content
        except Exception as e:
            logger.debug(f"Failed to read Docker secret {secret_name}: {e}")
        return None
    
    def _get_k8s_secret(self, secret_name: str) -> Optional[str]:
        """Read secret from Kubernetes mounted secrets"""
        try:
            # Kubernetes mounts secrets at /var/run/secrets
            k8s_path = Path("/var/run/secrets/minedu") / secret_name
            if k8s_path.exists():
                content = k8s_path.read_text().strip()
                logger.debug(f"Loaded Kubernetes secret: {secret_name}")
                return content
        except Exception as e:
            logger.debug(f"Failed to read Kubernetes secret {secret_name}: {e}")
        return None
    
    def _get_vault_secret(self, secret_name: str) -> Optional[str]:
        """Read secret from HashiCorp Vault"""
        if not self.vault_url or not self.vault_token:
            return None
        
        try:
            import hvac  # HashiCorp Vault client
            
            client = hvac.Client(url=self.vault_url, token=self.vault_token)
            if client.is_authenticated():
                secret_response = client.secrets.kv.v2.read_secret_version(
                    path=f"minedu/{secret_name}"
                )
                secret_value = secret_response['data']['data'].get(secret_name)
                if secret_value:
                    logger.debug(f"Loaded Vault secret: {secret_name}")
                    return secret_value
        except Exception as e:
            logger.debug(f"Failed to read Vault secret {secret_name}: {e}")
        return None
    
    def encrypt_secret(self, value: str) -> str:
        """Encrypt a secret value"""
        if not value:
            return ""
        encrypted = self.cipher.encrypt(value.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_secret(self, encrypted_value: str) -> str:
        """Decrypt a secret value"""
        if not encrypted_value:
            return ""
        try:
            decoded = base64.urlsafe_b64decode(encrypted_value.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt secret: {e}")
            return ""
    
    def get_database_url(self) -> str:
        """Get complete database URL from secrets"""
        db_user = self.get_secret("db_user", "postgres")
        db_password = self.get_secret("db_password", "")
        db_host = self.get_secret("db_host", "localhost")
        db_port = self.get_secret("db_port", "5432")
        db_name = self.get_secret("db_name", "minedu")
        
        if db_password:
            return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        else:
            return f"postgresql://{db_user}@{db_host}:{db_port}/{db_name}"
    
    def get_redis_url(self) -> str:
        """Get complete Redis URL from secrets"""
        redis_host = self.get_secret("redis_host", "localhost")
        redis_port = self.get_secret("redis_port", "6379")
        redis_password = self.get_secret("redis_password")
        redis_db = self.get_secret("redis_db", "0")
        
        if redis_password:
            return f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
        else:
            return f"redis://{redis_host}:{redis_port}/{redis_db}"
    
    def get_api_keys(self) -> Dict[str, str]:
        """Get all API keys from secrets"""
        return {
            'openai': self.get_secret("openai_api_key", ""),
            'anthropic': self.get_secret("anthropic_api_key", ""),
            'cohere': self.get_secret("cohere_api_key", ""),
            'huggingface': self.get_secret("huggingface_api_key", ""),
            'elasticsearch': self.get_secret("elasticsearch_api_key", "")
        }
    
    def get_jwt_secrets(self) -> Dict[str, str]:
        """Get JWT signing secrets"""
        return {
            'secret_key': self.get_secret("jwt_secret_key", "dev-secret-change-in-production"),
            'algorithm': self.get_secret("jwt_algorithm", "HS256"),
            'access_token_expire': self.get_secret("jwt_access_token_expire", "30")  # minutes
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security-related configuration"""
        return {
            'allowed_hosts': self.get_secret("allowed_hosts", "*").split(","),
            'cors_origins': self.get_secret("cors_origins", "*").split(","),
            'rate_limit_per_minute': int(self.get_secret("rate_limit_per_minute", "60")),
            'max_file_size_mb': int(self.get_secret("max_file_size_mb", "50")),
            'encryption_key': self.get_secret("encryption_key"),
            'session_timeout': int(self.get_secret("session_timeout", "3600"))
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check secrets availability"""
        secrets_status = {}
        
        # Test critical secrets
        critical_secrets = [
            "jwt_secret_key",
            "redis_password", 
            "db_password",
            "encryption_key"
        ]
        
        for secret_name in critical_secrets:
            secret_value = self.get_secret(secret_name)
            secrets_status[secret_name] = {
                'available': secret_value is not None,
                'source': self._get_secret_source(secret_name)
            }
        
        return {
            'secrets_manager': 'healthy',
            'docker_secrets_path': str(self.secrets_path),
            'docker_secrets_exists': self.secrets_path.exists(),
            'vault_configured': bool(self.vault_url),
            'secrets_status': secrets_status
        }
    
    def _get_secret_source(self, secret_name: str) -> str:
        """Determine where a secret is loaded from"""
        if self._get_docker_secret(secret_name):
            return "docker_secrets"
        elif self._get_k8s_secret(secret_name):
            return "kubernetes"
        elif self._get_vault_secret(secret_name):
            return "vault"
        elif os.getenv(secret_name.upper()):
            return "environment"
        else:
            return "not_found"

# Global secrets manager instance
_secrets_manager = None

def get_secrets_manager() -> SecretsManager:
    """Get global secrets manager instance"""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager

# Convenience functions
def get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    """Quick access to secrets"""
    return get_secrets_manager().get_secret(name, default)

def get_database_url() -> str:
    """Quick access to database URL"""
    return get_secrets_manager().get_database_url()

def get_redis_url() -> str:
    """Quick access to Redis URL"""
    return get_secrets_manager().get_redis_url()

def get_api_keys() -> Dict[str, str]:
    """Quick access to API keys"""
    return get_secrets_manager().get_api_keys()

# Environment-specific configuration loader
class SecureConfig:
    """Configuration class using secrets manager"""
    
    def __init__(self):
        self.secrets = get_secrets_manager()
    
    @property
    def database_url(self) -> str:
        return self.secrets.get_database_url()
    
    @property
    def redis_url(self) -> str:
        return self.secrets.get_redis_url()
    
    @property
    def api_keys(self) -> Dict[str, str]:
        return self.secrets.get_api_keys()
    
    @property
    def jwt_config(self) -> Dict[str, str]:
        return self.secrets.get_jwt_secrets()
    
    @property
    def security_config(self) -> Dict[str, Any]:
        return self.secrets.get_security_config()
    
    @property
    def environment(self) -> str:
        return self.secrets.get_secret("environment", "development")
    
    @property
    def debug(self) -> bool:
        return self.secrets.get_secret("debug", "false").lower() == "true"