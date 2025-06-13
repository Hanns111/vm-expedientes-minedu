"""
Seguridad específica para sistemas RAG y LLM
"""
import re
from typing import Dict, List, Optional
from src.core.config.security_config import SecurityConfig
from src.core.security.input_validator import SecurityError

class LLMSecurityGuard:
    """Seguridad específica para sistemas RAG y LLM"""
    
    # Prompts del sistema que no deben ser revelados
    SYSTEM_PROMPTS = {
        "eres un asistente",
        "tu función es",
        "debes responder",
        "tu rol es",
        "fuiste entrenado"
    }
    
    @classmethod
    def check_prompt_injection(cls, query: str) -> str:
        """
        Detecta y previene intentos de prompt injection
        
        Args:
            query: Consulta del usuario
            
        Returns:
            Query validada
            
        Raises:
            SecurityError: Si se detecta prompt injection
        """
        query_lower = query.lower()
        
        # Verificar intentos de revelar system prompt
        for pattern in cls.SYSTEM_PROMPTS:
            if pattern in query_lower and any(
                word in query_lower for word in ["muestra", "reveal", "show", "cuál es"]
            ):
                raise SecurityError("Intento de acceso a información del sistema detectado")
        
        # Verificar intentos de cambio de rol
        role_change_patterns = [
            r"ahora eres",
            r"actúa como",
            r"olvida todo",
            r"ignora las instrucciones",
            r"nuevo objetivo",
            r"tu nueva tarea"
        ]
        
        for pattern in role_change_patterns:
            if re.search(pattern, query_lower):
                raise SecurityError("Intento de manipulación del sistema detectado")
        
        return query
    
    @classmethod
    def sanitize_llm_response(cls, response: str) -> str:
        """
        Sanitiza respuestas del LLM para evitar filtración de información
        
        Args:
            response: Respuesta del modelo
            
        Returns:
            Respuesta sanitizada
        """
        # Remover referencias a rutas del sistema
        response = re.sub(r'[A-Za-z]:\\[\w\\\s]+', '[PATH_REMOVED]', response)
        response = re.sub(r'/[\w/]+/', '[PATH_REMOVED]', response)
        
        # Remover referencias a archivos del sistema
        system_files = [
            'vectorstore', 'pickle', '.pkl', '.json', 
            'config', 'settings', 'security', '.env'
        ]
        
        for file_ref in system_files:
            response = re.sub(
                rf'\b{re.escape(file_ref)}\b', 
                '[SYSTEM_FILE]', 
                response, 
                flags=re.IGNORECASE
            )
        
        # Remover posibles claves o tokens
        response = re.sub(r'\b[A-Za-z0-9]{32,}\b', '[TOKEN_REMOVED]', response)
        
        return response
    
    @classmethod
    def validate_context_injection(cls, contexts: List[Dict]) -> List[Dict]:
        """
        Valida que los contextos recuperados no contengan inyecciones
        
        Args:
            contexts: Lista de contextos del RAG
            
        Returns:
            Contextos validados
        """
        validated_contexts = []
        
        for context in contexts:
            # Verificar que el contexto no contenga instrucciones
            text = context.get('text', '').lower()
            
            # Saltar contextos con patrones peligrosos
            if any(pattern in text for pattern in SecurityConfig.DANGEROUS_PATTERNS):
                continue
            
            validated_contexts.append(context)
        
        return validated_contexts
    
    @classmethod
    def detect_jailbreak_attempts(cls, query: str) -> bool:
        """
        Detecta intentos de jailbreak en consultas
        
        Args:
            query: Consulta del usuario
            
        Returns:
            True si se detecta intento de jailbreak
        """
        query_lower = query.lower()
        
        jailbreak_patterns = [
            r"ignora.*instrucciones",
            r"olvida.*todo",
            r"eres.*libre",
            r"puedes.*hacer.*lo.*que.*quieras",
            r"actúa.*como.*si",
            r"pretende.*ser",
            r"simula.*ser",
            r"haz.*como.*si"
        ]
        
        for pattern in jailbreak_patterns:
            if re.search(pattern, query_lower):
                return True
        
        return False
    
    @classmethod
    def validate_response_length(cls, response: str, max_length: int = 2000) -> str:
        """
        Valida y limita la longitud de respuestas
        
        Args:
            response: Respuesta del modelo
            max_length: Longitud máxima permitida
            
        Returns:
            Respuesta truncada si es necesario
        """
        if len(response) > max_length:
            return response[:max_length] + "..."
        return response 