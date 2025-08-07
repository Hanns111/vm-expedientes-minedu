#!/usr/bin/env python3
"""
Configuración de logging estructurado para ELK Stack
Integración: Elasticsearch + Logstash + Kibana
"""

import logging
import logging.config
import json
import sys
from datetime import datetime
from typing import Dict, Any
import os

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'service': 'minedu-backend',
            'version': '1.3.0',
            'environment': os.getenv('ENVIRONMENT', 'development')
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'query'):
            log_entry['query'] = record.query
        if hasattr(record, 'processing_time'):
            log_entry['processing_time'] = record.processing_time
        if hasattr(record, 'ip_address'):
            log_entry['ip_address'] = record.ip_address
            
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry, ensure_ascii=False)

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': JSONFormatter,
        },
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'json',
            'stream': sys.stdout
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/minedu-backend.log',
            'formatter': 'json',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        },
        'elasticsearch': {
            'level': 'INFO',
            'class': 'logging.handlers.HTTPHandler',
            'host': os.getenv('ELASTICSEARCH_HOST', 'elasticsearch'),
            'url': '/minedu-logs-*/_doc',
            'method': 'POST',
            'formatter': 'json'
        }
    },
    'loggers': {
        'minedu': {
            'handlers': ['console', 'file', 'elasticsearch'],
            'level': 'DEBUG',
            'propagate': False
        },
        'fastapi': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False
        },
        'uvicorn': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
}

def setup_logging():
    """Initialize structured logging configuration"""
    # Ensure log directory exists
    os.makedirs('/app/logs', exist_ok=True)
    
    # Apply logging configuration
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # Get logger for this module
    logger = logging.getLogger('minedu.config')
    logger.info("Structured logging initialized", extra={
        'component': 'logging_config',
        'elk_enabled': True
    })
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance"""
    return logging.getLogger(f'minedu.{name}')

class LoggerAdapter(logging.LoggerAdapter):
    """Custom adapter for adding context to logs"""
    
    def __init__(self, logger: logging.Logger, extra: Dict[str, Any]):
        super().__init__(logger, extra)
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        # Merge extra data
        kwargs.setdefault('extra', {}).update(self.extra)
        return msg, kwargs

# Example usage functions
def log_search_query(logger: logging.Logger, query: str, user_id: str, 
                    processing_time: float, results_count: int):
    """Log search query with structured data"""
    logger.info("Search query executed", extra={
        'query': query,
        'user_id': user_id,
        'processing_time': processing_time,
        'results_count': results_count,
        'operation': 'search'
    })

def log_error_with_context(logger: logging.Logger, error: Exception, 
                          context: Dict[str, Any]):
    """Log error with full context"""
    logger.error(f"Error occurred: {str(error)}", extra={
        'error_type': type(error).__name__,
        'context': context,
        'operation': 'error_handling'
    }, exc_info=True)