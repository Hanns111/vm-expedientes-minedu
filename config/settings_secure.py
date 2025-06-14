"""
Configuración segura para producción MINEDU
Variables de entorno y configuraciones de seguridad
"""

import os
from pathlib import Path
from typing import Dict, Any

# Configuración base
BASE_DIR = Path(__file__).resolve().parent.parent
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Configuración de seguridad
SECURITY_CONFIG = {
    'SECRET_KEY': os.getenv('SECRET_KEY', 'your-secret-key-change-in-production'),
    'DEBUG': os.getenv('DEBUG', 'False').lower() == 'true',
    'ALLOWED_HOSTS': os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(','),
    'CSRF_TRUSTED_ORIGINS': os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000').split(','),
}

# Configuración de base de datos (si se implementa)
DATABASE_CONFIG = {
    'ENGINE': os.getenv('DB_ENGINE', 'sqlite'),
    'NAME': os.getenv('DB_NAME', BASE_DIR / 'data' / 'minedu.db'),
    'USER': os.getenv('DB_USER', ''),
    'PASSWORD': os.getenv('DB_PASSWORD', ''),
    'HOST': os.getenv('DB_HOST', 'localhost'),
    'PORT': os.getenv('DB_PORT', '5432'),
}

# Configuración de logging
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'app.log',
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'security': {
            'handlers': ['security_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Configuración de rate limiting
RATE_LIMITING = {
    'REQUESTS_PER_MINUTE': int(os.getenv('RATE_LIMIT_PER_MINUTE', '30')),
    'REQUESTS_PER_HOUR': int(os.getenv('RATE_LIMIT_PER_HOUR', '500')),
    'REQUESTS_PER_DAY': int(os.getenv('RATE_LIMIT_PER_DAY', '2000')),
    'BURST_LIMIT': int(os.getenv('RATE_LIMIT_BURST', '10')),
}

# Configuración de validación
VALIDATION_CONFIG = {
    'MAX_QUERY_LENGTH': int(os.getenv('MAX_QUERY_LENGTH', '512')),
    'MAX_FILE_SIZE_MB': int(os.getenv('MAX_FILE_SIZE_MB', '100')),
    'MAX_RESULTS_PER_QUERY': int(os.getenv('MAX_RESULTS_PER_QUERY', '100')),
    'ALLOWED_FILE_EXTENSIONS': os.getenv('ALLOWED_EXTENSIONS', '.pdf,.txt,.docx,.json,.pkl').split(','),
}

# Configuración de privacidad
PRIVACY_CONFIG = {
    'ENABLE_PII_DETECTION': os.getenv('ENABLE_PII_DETECTION', 'True').lower() == 'true',
    'MASK_PII_IN_LOGS': os.getenv('MASK_PII_IN_LOGS', 'True').lower() == 'true',
    'RETENTION_DAYS': int(os.getenv('LOG_RETENTION_DAYS', '30')),
}

# Configuración de monitoreo
MONITORING_CONFIG = {
    'ENABLE_MONITORING': os.getenv('ENABLE_MONITORING', 'True').lower() == 'true',
    'ALERT_EMAIL': os.getenv('ALERT_EMAIL', 'admin@minedu.gob.pe'),
    'ALERT_THRESHOLD': int(os.getenv('ALERT_THRESHOLD', '10')),
}

# Configuración de compliance
COMPLIANCE_CONFIG = {
    'ENABLE_AUDIT_LOG': os.getenv('ENABLE_AUDIT_LOG', 'True').lower() == 'true',
    'AUDIT_RETENTION_DAYS': int(os.getenv('AUDIT_RETENTION_DAYS', '365')),
    'COMPLIANCE_STANDARD': os.getenv('COMPLIANCE_STANDARD', 'ISO27001'),
}

# Configuración de archivos
FILE_CONFIG = {
    'UPLOAD_DIR': BASE_DIR / 'data' / 'uploads',
    'PROCESSED_DIR': BASE_DIR / 'data' / 'processed',
    'BACKUP_DIR': BASE_DIR / 'data' / 'backups',
    'TEMP_DIR': BASE_DIR / 'data' / 'temp',
}

# Configuración de vectorstore
VECTORSTORE_CONFIG = {
    'MODEL_NAME': os.getenv('VECTORSTORE_MODEL', 'sentence-transformers/all-MiniLM-L6-v2'),
    'EMBEDDING_DIMENSION': int(os.getenv('EMBEDDING_DIMENSION', '384')),
    'SIMILARITY_THRESHOLD': float(os.getenv('SIMILARITY_THRESHOLD', '0.7')),
    'MAX_VECTORS': int(os.getenv('MAX_VECTORS', '10000')),
}

# Configuración de caché
CACHE_CONFIG = {
    'ENABLE_CACHE': os.getenv('ENABLE_CACHE', 'True').lower() == 'true',
    'CACHE_TTL': int(os.getenv('CACHE_TTL', '3600')),  # 1 hora
    'CACHE_MAX_SIZE': int(os.getenv('CACHE_MAX_SIZE', '1000')),
}

def get_config() -> Dict[str, Any]:
    """
    Obtener configuración completa del sistema
    
    Returns:
        Dict: Configuración completa
    """
    return {
        'environment': ENVIRONMENT,
        'base_dir': str(BASE_DIR),
        'security': SECURITY_CONFIG,
        'database': DATABASE_CONFIG,
        'logging': LOGGING_CONFIG,
        'rate_limiting': RATE_LIMITING,
        'validation': VALIDATION_CONFIG,
        'privacy': PRIVACY_CONFIG,
        'monitoring': MONITORING_CONFIG,
        'compliance': COMPLIANCE_CONFIG,
        'files': {k: str(v) for k, v in FILE_CONFIG.items()},
        'vectorstore': VECTORSTORE_CONFIG,
        'cache': CACHE_CONFIG,
    }

def validate_config() -> bool:
    """
    Validar configuración de seguridad
    
    Returns:
        bool: True si la configuración es válida
    """
    try:
        config = get_config()
        
        # Verificar variables críticas
        if config['environment'] == 'production':
            if config['security']['SECRET_KEY'] == 'your-secret-key-change-in-production':
                print("⚠️ ADVERTENCIA: SECRET_KEY no configurada para producción")
                return False
            
            if config['security']['DEBUG']:
                print("⚠️ ADVERTENCIA: DEBUG habilitado en producción")
                return False
        
        # Verificar directorios
        for dir_name, dir_path in config['files'].items():
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        # Verificar límites de seguridad
        if config['rate_limiting']['REQUESTS_PER_MINUTE'] > 100:
            print("⚠️ ADVERTENCIA: Rate limit muy alto")
            return False
        
        if config['validation']['MAX_FILE_SIZE_MB'] > 500:
            print("⚠️ ADVERTENCIA: Tamaño máximo de archivo muy alto")
            return False
        
        print("✅ Configuración validada correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error validando configuración: {e}")
        return False

if __name__ == "__main__":
    # Validar configuración al ejecutar directamente
    if validate_config():
        print("Configuración de seguridad lista")
    else:
        print("Configuración de seguridad requiere ajustes") 