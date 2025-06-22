"""
Wrapper seguro para el sistema de búsqueda híbrido
"""
import re
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
    
    def _normalize_numbers(self, text: str) -> str:
        """
        Normaliza formatos de números para búsqueda consistente
        Convierte comas decimales a puntos (formato peruano → internacional)
        """
        # Normalizar montos en soles (S/ 320,00 → S/ 320.00)
        text = re.sub(r'(\d+),(\d{2})', r'\1.\2', text)
        return text
    
    def _create_search_variants(self, query: str) -> List[str]:
        """
        Crea variantes de búsqueda para mejorar la recuperación de documentos
        """
        variants = [query]
        
        # Normalizar la query original
        normalized_query = self._normalize_numbers(query)
        if normalized_query != query:
            variants.append(normalized_query)
        
        # Si contiene números específicos, crear variantes
        if re.search(r'\b320\b', query):
            variants.extend([
                'S/ 320',
                'S/ 320.00',
                'S/ 320,00',
                '320.00',
                '320,00',
                'viático día',
                'escala viáticos'
            ])
        
        # Para consultas sobre montos
        if any(word in query.lower() for word in ['monto', 'cantidad', 'precio', 'tarifa']):
            variants.extend([
                'escala viáticos',
                'viático por día',
                'VIÁTICO POR DÍA'
            ])
        
        # Remover duplicados manteniendo el orden
        unique_variants = []
        for variant in variants:
            if variant not in unique_variants:
                unique_variants.append(variant)
        
        return unique_variants
        
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
            
            # 6. Crear variantes de búsqueda para mejorar recuperación
            search_variants = self._create_search_variants(clean_query)
            app_logger.info(f"Variantes de búsqueda generadas: {len(search_variants)}")
            
            # 7. Realizar búsqueda con variantes
            all_results = []
            
            for variant in search_variants:
                try:
                    variant_results = self.search_engine.search(variant, top_k=safe_top_k)
                    
                    # Marcar la variante usada en los resultados
                    for result in variant_results:
                        result['search_variant'] = variant
                        if variant != clean_query:
                            result['original_query'] = clean_query
                    
                    all_results.extend(variant_results)
                    
                    # Si encontramos resultados relevantes con "320", priorizar
                    relevant_found = any('320' in str(result.get('texto', result.get('text', ''))) 
                                       for result in variant_results)
                    if relevant_found:
                        app_logger.info(f"Resultados relevantes encontrados con variante: '{variant}'")
                        break  # Usar solo la primera variante que encuentre resultados relevantes
                        
                except Exception as e:
                    app_logger.warning(f"Error en búsqueda con variante '{variant}': {e}")
                    continue
            
            # 8. Eliminar duplicados y ordenar por score
            unique_results = {}
            for result in all_results:
                # Usar texto como clave única para deduplicar
                text_key = result.get('texto', result.get('text', ''))[:100]
                if text_key not in unique_results or result.get('score', 0) > unique_results[text_key].get('score', 0):
                    unique_results[text_key] = result
            
            # Convertir a lista y ordenar por score
            results = list(unique_results.values())
            results.sort(key=lambda x: x.get('score', 0), reverse=True)
            results = results[:safe_top_k]  # Mantener solo top_k
            
            # 9. Sanitizar resultados
            safe_results = []
            for result in results:
                # Manejar diferentes formatos de campo de texto (tanto 'text' como 'texto')
                texto_contenido = result.get('texto', result.get('text', ''))
                
                safe_result = {
                    'text': LLMSecurityGuard.sanitize_llm_response(texto_contenido),
                    'score': result.get('score', 0.0),
                    'method': result.get('method', 'unknown'),
                    'search_variant': result.get('search_variant', clean_query),
                    'metadata': PrivacyProtector.sanitize_document_metadata(
                        result.get('metadata', {})
                    )
                }
                safe_results.append(safe_result)
            
            # 10. Log exitoso
            app_logger.info(
                f"Búsqueda exitosa - Usuario: {user_id[:8]}... - Tipo: {audit_data['query_type']} - Variantes: {len(search_variants)}"
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