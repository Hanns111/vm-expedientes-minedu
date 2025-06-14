"""
Configuración centralizada de seguridad para MINEDU
Define todas las constantes y configuraciones de seguridad
"""
from pathlib import Path
import os
import re
import hashlib
import secrets
from datetime import datetime
from typing import Set, Dict, Any
import logging

class SecurityConfig:
    """Configuración centralizada de seguridad para MINEDU"""
    
    # Versión del sistema de seguridad
    SECURITY_VERSION = "1.0.1"
    
    # Rutas base (NUNCA usar rutas absolutas)
    BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    
    # Límites de seguridad
    MAX_QUERY_LENGTH = 512
    MAX_FILE_SIZE_MB = 100
    MAX_RESULTS_PER_QUERY = 100
    
    # Rate limiting
    REQUESTS_PER_MINUTE = 30
    REQUESTS_PER_HOUR = 500
    REQUESTS_PER_DAY = 2000
    
    # Validación de archivos
    ALLOWED_FILE_EXTENSIONS: Set[str] = {'.pdf', '.txt', '.docx', '.json', '.pkl'}
    ALLOWED_MIME_TYPES: Set[str] = {
        'application/pdf',
        'text/plain',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/json',
        'application/octet-stream'
    }
    
    # Patrones peligrosos para LLM/RAG
    DANGEROUS_PATTERNS: Set[str] = {
        "ignore previous instructions",
        "olvidar instrucciones anteriores",
        "system prompt",
        "eres un",
        "actúa como",
        "forget all",
        "nuevo rol",
        "reveal system",
        "show config"
    }
    
    # Patrones de SQL Injection
    SQL_INJECTION_PATTERNS: Set[str] = {
        "union", "select", "drop", "insert", "update", "delete",
        "--", "/*", "*/", "xp_", "sp_", "@@", "char(", "nchar(",
        "sysobjects", "syscolumns"
    }
    
    # Datos sensibles a enmascarar
    PII_PATTERNS: Dict[str, str] = {
        r'\b\d{8}\b': '[DNI_REMOVED]',                    # DNI peruano
        r'\b\d{11}\b': '[RUC_REMOVED]',                   # RUC
        r'\b\d{9}\b': '[PHONE_REMOVED]',                  # Teléfono
        r'[\w\.-]+@[\w\.-]+': '[EMAIL_REMOVED]',          # Email
        r'\b[A-Z][a-z]+ [A-Z][a-z]+\b': '[NAME_REMOVED]'  # Nombres
    }
    
    # Horarios permitidos (hora local Perú)
    ALLOWED_HOURS = {
        'start': 7,  # 7 AM
        'end': 20    # 8 PM
    }
    
    # Configuración de logs
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    AUDIT_LOG_FILE = LOGS_DIR / "audit.log"
    SECURITY_LOG_FILE = LOGS_DIR / "security.log"
    
    # Rutas de archivos del sistema
    VECTORSTORE_PATH = DATA_DIR / "processed" / "vectorstore_semantic_full_v2.pkl"
    CHUNKS_PATH = DATA_DIR / "processed" / "chunks_v2.json"
    
    def __init__(self):
        """Inicializar configuración de seguridad"""
        self.session_id = secrets.token_hex(16)
        self.created_at = datetime.now()
        self._setup_logging()
        self._ensure_directories()
    
    def _setup_logging(self):
        """Configurar sistema de logging de seguridad"""
        # Crear directorio de logs si no existe
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Configurar logger de seguridad
        self.security_logger = logging.getLogger('SecurityConfig')
        self.security_logger.setLevel(logging.INFO)
        
        # Handler para archivo de seguridad
        if not self.security_logger.handlers:
            file_handler = logging.FileHandler(self.SECURITY_LOG_FILE, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - SESSION:%(session_id)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            self.security_logger.addHandler(file_handler)
    
    def _ensure_directories(self):
        """Crear directorios necesarios si no existen"""
        directories = [self.DATA_DIR, self.LOGS_DIR]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def validate_path(self, file_path: str, category: str = 'data') -> bool:
        """
        Validar que una ruta sea segura.
        
        Args:
            file_path: Ruta a validar
            category: Categoría de archivo ('data', 'documents', 'code', 'results')
            
        Returns:
            bool: True si la ruta es segura
        """
        try:
            path = Path(file_path).resolve()
            
            # Verificar que esté dentro del directorio base del proyecto
            if not path.is_relative_to(self.BASE_DIR):
                self.log_security_event('path_validation_failed', {
                    'file_path': file_path,
                    'reason': 'Path outside project directory'
                })
                return False
            
            # Verificar patrones peligrosos en la ruta
            path_str = str(path).lower()
            dangerous_patterns = ['..', '~', '/etc', '/var', '/usr', 'c:\\windows']
            for pattern in dangerous_patterns:
                if pattern in path_str:
                    self.log_security_event('path_validation_failed', {
                        'file_path': file_path,
                        'reason': f'Dangerous pattern detected: {pattern}'
                    })
                    return False
            
            # Verificar extensión si el archivo existe o se especifica
            if path.suffix and category in ['data', 'documents']:
                if path.suffix.lower() not in self.ALLOWED_FILE_EXTENSIONS:
                    self.log_security_event('path_validation_failed', {
                        'file_path': file_path,
                        'reason': f'Extension not allowed: {path.suffix}'
                    })
                    return False
            
            # Verificar tamaño si el archivo existe
            if path.exists() and path.is_file():
                file_size = path.stat().st_size
                max_size = self.MAX_FILE_SIZE_MB * 1024 * 1024
                if file_size > max_size:
                    self.log_security_event('path_validation_failed', {
                        'file_path': file_path,
                        'reason': f'File too large: {file_size} bytes'
                    })
                    return False
            
            self.log_security_event('path_validation_success', {
                'file_path': file_path,
                'category': category
            })
            return True
            
        except Exception as e:
            self.log_security_event('path_validation_error', {
                'file_path': file_path,
                'error': str(e)
            })
            return False
    
    def sanitize_input(self, user_input: str) -> str:
        """
        Sanitizar entrada de usuario.
        
        Args:
            user_input: Texto de entrada del usuario
            
        Returns:
            str: Texto sanitizado
        """
        if not isinstance(user_input, str):
            user_input = str(user_input)
        
        original_input = user_input
        
        # Limitar longitud
        if len(user_input) > self.MAX_QUERY_LENGTH:
            user_input = user_input[:self.MAX_QUERY_LENGTH]
            self.log_security_event('input_truncated', {
                'original_length': len(original_input),
                'truncated_length': len(user_input)
            })
        
        # Remover patrones peligrosos
        for pattern in self.DANGEROUS_PATTERNS:
            user_input = re.sub(pattern, '', user_input, flags=re.IGNORECASE)
        
        # Remover patrones de SQL injection
        for pattern in self.SQL_INJECTION_PATTERNS:
            user_input = re.sub(pattern, '', user_input, flags=re.IGNORECASE)
        
        # Remover caracteres peligrosos
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\x1a']
        for char in dangerous_chars:
            user_input = user_input.replace(char, '')
        
        # Normalizar espacios
        user_input = re.sub(r'\s+', ' ', user_input.strip())
        
        # Log si se realizaron cambios
        if original_input != user_input:
            self.log_security_event('input_sanitized', {
                'original_input': original_input[:100],
                'sanitized_input': user_input[:100]
            })
        
        return user_input
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        Obtener resumen de configuración de seguridad.
        
        Returns:
            Dict: Resumen de configuración
        """
        return {
            'version': self.SECURITY_VERSION,
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'base_dir': str(self.BASE_DIR),
            'data_dir': str(self.DATA_DIR),
            'logs_dir': str(self.LOGS_DIR),
            'limits': {
                'max_query_length': self.MAX_QUERY_LENGTH,
                'max_file_size_mb': self.MAX_FILE_SIZE_MB,
                'max_results_per_query': self.MAX_RESULTS_PER_QUERY
            },
            'rate_limiting': {
                'requests_per_minute': self.REQUESTS_PER_MINUTE,
                'requests_per_hour': self.REQUESTS_PER_HOUR,
                'requests_per_day': self.REQUESTS_PER_DAY
            },
            'allowed_extensions': list(self.ALLOWED_FILE_EXTENSIONS),
            'dangerous_patterns_count': len(self.DANGEROUS_PATTERNS),
            'sql_injection_patterns_count': len(self.SQL_INJECTION_PATTERNS),
            'pii_patterns_count': len(self.PII_PATTERNS)
        }
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """
        Registrar evento de seguridad.
        
        Args:
            event_type: Tipo de evento ('access', 'error', 'warning', 'audit')
            details: Detalles del evento
        """
        event_data = {
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'event_type': event_type,
            'details': details
        }
        
        self.security_logger.info(f"SECURITY_EVENT: {event_data}")
    
    @classmethod
    def get_safe_path(cls, relative_path: str) -> Path:
        """Retorna una ruta segura validada dentro del proyecto"""
        path = cls.BASE_DIR / relative_path
        if not path.resolve().is_relative_to(cls.BASE_DIR):
            raise SecurityError(f"Intento de acceso fuera del directorio base: {relative_path}")
        return path

class SecurityError(Exception):
    """Excepción para errores de seguridad"""
    pass 