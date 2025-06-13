"""
Logger seguro con sanitización automática
"""
import logging
import re
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
from src.core.config.security_config import SecurityConfig
from src.core.security.privacy import PrivacyProtector

class SecurityFilter(logging.Filter):
    """Filtro para sanitizar logs y remover información sensible"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Sanitizar el mensaje
        if hasattr(record, 'msg'):
            record.msg = PrivacyProtector.remove_pii(str(record.msg))
        
        # Sanitizar argumentos
        if hasattr(record, 'args') and record.args:
            sanitized_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    sanitized_args.append(PrivacyProtector.remove_pii(arg))
                else:
                    sanitized_args.append(arg)
            record.args = tuple(sanitized_args)
        
        return True

class SecureLogger:
    """Logger seguro con sanitización automática"""
    
    @staticmethod
    def setup_logger(
        name: str,
        log_file: Path,
        level: str = 'INFO',
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ) -> logging.Logger:
        """
        Configura un logger seguro con rotación de archivos
        
        Args:
            name: Nombre del logger
            log_file: Archivo de log
            level: Nivel de logging
            max_bytes: Tamaño máximo del archivo antes de rotar
            backup_count: Número de backups a mantener
            
        Returns:
            Logger configurado
        """
        # Crear directorio si no existe
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Crear logger
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        # Evitar duplicación de handlers
        if logger.handlers:
            return logger
        
        # Formato seguro (sin información sensible)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler con rotación
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        
        # Agregar filtro de seguridad
        security_filter = SecurityFilter()
        file_handler.addFilter(security_filter)
        
        # Agregar handler al logger
        logger.addHandler(file_handler)
        
        # También log a consola en desarrollo (con filtro)
        if SecurityConfig.LOG_LEVEL == 'DEBUG':
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.addFilter(security_filter)
            logger.addHandler(console_handler)
        
        return logger

# Crear loggers principales
app_logger = SecureLogger.setup_logger(
    'minedu_app',
    SecurityConfig.LOGS_DIR / 'app.log',
    level=SecurityConfig.LOG_LEVEL
)

security_logger = SecureLogger.setup_logger(
    'minedu_security',
    SecurityConfig.SECURITY_LOG_FILE,
    level='INFO'  # Siempre INFO o superior para seguridad
)

audit_logger = SecureLogger.setup_logger(
    'minedu_audit',
    SecurityConfig.AUDIT_LOG_FILE,
    level='INFO'  # Siempre INFO para auditoría
) 