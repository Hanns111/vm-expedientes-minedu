"""
Wrapper seguro para el sistema de búsqueda híbrido
"""
from typing import List, Dict, Optional, Tuple
from src.core.hybrid.hybrid_search import HybridSearch
from src.core.security.input_validator import InputValidator, SecurityError
from src.core.security.llm_security import LLMSecurityGuard
from src.core.security.rate_limiter import rate_limiter
from src.core.security.privacy import PrivacyProtector
from src.core.security.compliance import compliance_logger, AuditEventType
from src.core.security.monitor import security_monitor
from src.core.security.logger import app_logger
from src.core.config.security_config import SecurityConfig

class SecureHybridSearch:
    """Búsqueda híbrida con todas las medidas de seguridad implementadas"""
    
    def __init__(self):
        # Usar rutas seguras de configuración
        bm25_path = str(SecurityConfig.DATA_DIR / "processed" / "vectorstore_bm25_test.pkl")
        tfidf_path = str(SecurityConfig.VECTORSTORE_PATH)
        transformer_path = str(SecurityConfig.DATA_DIR / "processed" / "vectorstore_transformers_test.pkl")
        
        try:
            self.search_engine = HybridSearch(
                bm25_vectorstore_path=bm25_path,
                tfidf_vectorstore_path=tfidf_path,
                transformer_vectorstore_path=transformer_path,
                fusion_strategy='weighted'
            )
            app_logger.info("SecureHybridSearch inicializado correctamente")
        except Exception as e:
            app_logger.error(f"Error inicializando HybridSearch: {e}")
            # Fallback: usar solo TF-IDF si los otros fallan
            self.search_engine = HybridSearch(
                bm25_vectorstore_path=bm25_path,
                tfidf_vectorstore_path=tfidf_path,
                transformer_vectorstore_path=tfidf_path,  # Usar TF-IDF como fallback
                fusion_strategy='simple'
            )
        
    def search(
        self,
        query: str,
        user_id: str,
        ip_address: str,
        session_id: str,
        top_k: int = 5
    ) -> Tuple[List[Dict], Optional[str]]:
        """
        Realiza una búsqueda segura con todas las validaciones
        
        Args:
            query: Consulta del usuario
            user_id: ID del usuario
            ip_address: IP del usuario
            session_id: ID de sesión
            top_k: Número de resultados
            
        Returns:
            (resultados, mensaje_error)
        """
        try:
            # 1. Verificar rate limit
            allowed, error_msg = rate_limiter.check_rate_limit(user_id)
            if not allowed:
                compliance_logger.log_audit_event(
                    AuditEventType.ACCESS_DENIED,
                    user_id=user_id,
                    details={'reason': 'rate_limit', 'message': error_msg},
                    ip_address=ip_address,
                    session_id=session_id
                )
                return [], error_msg
            
            # 2. Verificar IP bloqueada
            if security_monitor.is_ip_blocked(ip_address):
                compliance_logger.log_audit_event(
                    AuditEventType.ACCESS_DENIED,
                    user_id=user_id,
                    details={'reason': 'blocked_ip'},
                    ip_address=ip_address,
                    session_id=session_id
                )
                return [], "Acceso denegado"
            
            # 3. Sanitizar y validar entrada
            clean_query = InputValidator.sanitize_query(query)
            clean_query = LLMSecurityGuard.check_prompt_injection(clean_query)
            safe_top_k = InputValidator.validate_top_k(top_k)
            
            # 4. Monitorear consulta
            security_monitor.monitor_query(user_id, clean_query, ip_address)
            
            # 5. Log de auditoría (anonimizado)
            audit_data = PrivacyProtector.anonymize_query_for_logging(query, user_id)
            compliance_logger.log_audit_event(
                AuditEventType.SEARCH,
                user_id=user_id,
                details={
                    'query_type': audit_data['query_type'],
                    'query_length': audit_data['query_length'],
                    'resource': 'hybrid_search'
                },
                ip_address=ip_address,
                session_id=session_id
            )
            
            # 6. Realizar búsqueda
            results = self.search_engine.search(clean_query, top_k=safe_top_k)
            
            # 7. Sanitizar resultados
            safe_results = []
            for result in results:
                safe_result = {
                    'text': LLMSecurityGuard.sanitize_llm_response(result.get('text', '')),
                    'score': result.get('score', 0.0),
                    'method': result.get('method', 'unknown'),
                    'metadata': PrivacyProtector.sanitize_document_metadata(
                        result.get('metadata', {})
                    )
                }
                safe_results.append(safe_result)
            
            # 8. Log exitoso
            app_logger.info(
                f"Búsqueda exitosa - Usuario: {user_id[:8]}... - Tipo: {audit_data['query_type']}"
            )
            
            return safe_results, None
            
        except SecurityError as e:
            # Log de intento de ataque
            compliance_logger.log_security_event(
                severity="WARNING",
                event_description=f"Intento de ataque detectado: {str(e)}",
                user_id=user_id,
                additional_info={'ip': ip_address}
            )
            return [], "Consulta no válida"
            
        except Exception as e:
            # Log de error
            app_logger.error(f"Error en búsqueda segura: {str(e)}")
            compliance_logger.log_audit_event(
                AuditEventType.ERROR,
                user_id=user_id,
                details={'error': str(e)[:100]},  # Limitar longitud
                ip_address=ip_address,
                session_id=session_id
            )
            return [], "Error en el sistema" 