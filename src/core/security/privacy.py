"""
Protección de datos personales y privacidad
"""
import re
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
from src.core.config.security_config import SecurityConfig

class PrivacyProtector:
    """Protección de datos personales y privacidad"""
    
    @staticmethod
    def anonymize_user_data(user_id: str, user_ip: Optional[str] = None) -> Dict[str, str]:
        """
        Anonimiza datos del usuario para almacenamiento
        
        Args:
            user_id: ID del usuario
            user_ip: IP del usuario (opcional)
            
        Returns:
            Datos anonimizados
        """
        # Hash irreversible del ID
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:16]
        
        # Anonimizar IP (mantener solo primeros 2 octetos para geolocalización aproximada)
        anon_ip = None
        if user_ip:
            ip_parts = user_ip.split('.')
            if len(ip_parts) == 4:
                anon_ip = f"{ip_parts[0]}.{ip_parts[1]}.x.x"
        
        return {
            'user_hash': user_hash,
            'anon_ip': anon_ip,
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def remove_pii(text: str) -> str:
        """
        Remueve información personal identificable del texto
        
        Args:
            text: Texto a limpiar
            
        Returns:
            Texto sin PII
        """
        # Aplicar todos los patrones de PII
        for pattern, replacement in SecurityConfig.PII_PATTERNS.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    @staticmethod
    def anonymize_query_for_logging(query: str, user_id: str) -> Dict[str, Any]:
        """
        Anonimiza una consulta para logging y análisis
        
        Args:
            query: Consulta original
            user_id: ID del usuario
            
        Returns:
            Datos anonimizados para logging
        """
        # Remover PII de la consulta
        clean_query = PrivacyProtector.remove_pii(query)
        
        # Clasificar tipo de consulta sin guardar contenido
        query_type = PrivacyProtector._classify_query_type(query)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'user_hash': hashlib.sha256(user_id.encode()).hexdigest()[:16],
            'query_length': len(query),
            'query_type': query_type,
            'has_pii': clean_query != query,  # Indicar si contenía PII
            # NO guardar la consulta original ni limpia
        }
    
    @staticmethod
    def _classify_query_type(query: str) -> str:
        """Clasifica el tipo de consulta sin revelar contenido"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['monto', 'cuánto', 'precio', 'costo']):
            return 'financial'
        elif any(word in query_lower for word in ['procedimiento', 'cómo', 'pasos']):
            return 'procedural'
        elif any(word in query_lower for word in ['quién', 'responsable', 'encargado']):
            return 'responsibility'
        elif any(word in query_lower for word in ['cuándo', 'plazo', 'fecha', 'tiempo']):
            return 'temporal'
        elif any(word in query_lower for word in ['dónde', 'lugar', 'ubicación']):
            return 'location'
        else:
            return 'general'
    
    @staticmethod
    def sanitize_document_metadata(metadata: Dict) -> Dict:
        """Sanitiza metadata de documentos antes de mostrar al usuario"""
        safe_metadata = {}
        
        # Solo incluir campos seguros
        safe_fields = ['title', 'date', 'type', 'category', 'pages']
        
        for field in safe_fields:
            if field in metadata:
                # Remover PII incluso de metadata
                safe_metadata[field] = PrivacyProtector.remove_pii(str(metadata[field]))
        
        return safe_metadata
    
    @staticmethod
    def create_audit_trail(user_id: str, action: str, resource: str, success: bool = True) -> Dict[str, Any]:
        """
        Crea una entrada de auditoría anonimizada
        
        Args:
            user_id: ID del usuario
            action: Acción realizada
            resource: Recurso accedido
            success: Si la acción fue exitosa
            
        Returns:
            Entrada de auditoría anonimizada
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'user_hash': hashlib.sha256(user_id.encode()).hexdigest()[:16],
            'action': action,
            'resource': resource,
            'success': success,
            'session_id': hashlib.sha256(f"{user_id}_{datetime.now().strftime('%Y%m%d')}".encode()).hexdigest()[:12]
        }
    
    @staticmethod
    def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enmascara datos sensibles en un diccionario
        
        Args:
            data: Diccionario con datos potencialmente sensibles
            
        Returns:
            Diccionario con datos enmascarados
        """
        sensitive_keys = ['password', 'token', 'key', 'secret', 'credential', 'dni', 'ruc']
        masked_data = {}
        
        for key, value in data.items():
            key_lower = key.lower()
            
            # Enmascarar valores de claves sensibles
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                if isinstance(value, str):
                    masked_data[key] = '*' * min(len(value), 8) + '...'
                else:
                    masked_data[key] = '[MASKED]'
            else:
                # Para otros campos, aplicar sanitización de PII si es string
                if isinstance(value, str):
                    masked_data[key] = PrivacyProtector.remove_pii(value)
                else:
                    masked_data[key] = value
        
        return masked_data 