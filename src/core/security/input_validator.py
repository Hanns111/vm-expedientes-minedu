"""
Validador y sanitizador de entradas para prevenir ataques
"""
import re
from html import escape
from typing import Optional, List
from pathlib import Path
from src.core.config.security_config import SecurityConfig, SecurityError

class InputValidator:
    """Validador y sanitizador de entradas para prevenir ataques"""
    
    @staticmethod
    def sanitize_query(query: str) -> str:
        """
        Sanitiza una consulta de búsqueda eliminando elementos peligrosos
        
        Args:
            query: Consulta del usuario
            
        Returns:
            Consulta sanitizada
            
        Raises:
            SecurityError: Si se detecta un intento de ataque
        """
        if not isinstance(query, str):
            return ""
        
        # Verificar longitud
        if len(query) > SecurityConfig.MAX_QUERY_LENGTH:
            query = query[:SecurityConfig.MAX_QUERY_LENGTH]
        
        # Verificar patrones peligrosos de LLM
        query_lower = query.lower()
        for pattern in SecurityConfig.DANGEROUS_PATTERNS:
            if pattern in query_lower:
                raise SecurityError(f"Patrón peligroso detectado: {pattern}")
        
        # Verificar SQL injection
        for pattern in SecurityConfig.SQL_INJECTION_PATTERNS:
            if pattern in query_lower:
                raise SecurityError(f"Posible SQL injection detectado: {pattern}")
        
        # Eliminar caracteres peligrosos pero preservar acentos y ñ
        # Permite: letras, números, espacios, acentos, ñ, puntuación básica
        query = re.sub(r'[^\w\s\-.,?¿!¡áéíóúÁÉÍÓÚñÑ]', '', query)
        
        # Eliminar espacios múltiples
        query = re.sub(r'\s+', ' ', query)
        
        # Escapar HTML
        query = escape(query)
        
        return query.strip()
    
    @staticmethod
    def validate_filename(filename: str) -> bool:
        """Valida que un nombre de archivo sea seguro"""
        # Solo permitir caracteres alfanuméricos, guiones y puntos
        if not re.match(r'^[\w\-. ]+$', filename):
            return False
        
        # Verificar extensión
        extension = Path(filename).suffix.lower()
        if extension not in SecurityConfig.ALLOWED_FILE_EXTENSIONS:
            return False
        
        # Prevenir path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        
        return True
    
    @staticmethod
    def validate_top_k(top_k: int) -> int:
        """Valida y limita el número de resultados solicitados"""
        if not isinstance(top_k, int) or top_k < 1:
            return 5  # Valor por defecto
        
        return min(top_k, SecurityConfig.MAX_RESULTS_PER_QUERY)
    
    @staticmethod
    def validate_user_id(user_id: str) -> bool:
        """Valida que un ID de usuario sea seguro"""
        if not isinstance(user_id, str) or len(user_id) == 0:
            return False
        
        # Solo permitir caracteres alfanuméricos, guiones y guiones bajos
        if not re.match(r'^[\w\-_]+$', user_id):
            return False
        
        # Limitar longitud
        if len(user_id) > 100:
            return False
        
        return True
    
    @staticmethod
    def validate_ip_address(ip_address: str) -> bool:
        """Valida formato de IP address"""
        if not isinstance(ip_address, str):
            return False
        
        # Patrón básico para IPv4
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(ip_pattern, ip_address):
            return False
        
        # Verificar que cada octeto esté en rango válido
        try:
            octets = ip_address.split('.')
            for octet in octets:
                if not (0 <= int(octet) <= 255):
                    return False
        except ValueError:
            return False
        
        return True 