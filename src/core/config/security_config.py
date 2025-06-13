"""
Configuración centralizada de seguridad para MINEDU
Define todas las constantes y configuraciones de seguridad
"""
from pathlib import Path
import os
from typing import Set, Dict

class SecurityConfig:
    """Configuración centralizada de seguridad para MINEDU"""
    
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
    ALLOWED_FILE_EXTENSIONS: Set[str] = {'.pdf', '.txt', '.docx'}
    ALLOWED_MIME_TYPES: Set[str] = {
        'application/pdf',
        'text/plain',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
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