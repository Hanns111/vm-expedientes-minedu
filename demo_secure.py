#!/usr/bin/env python3
"""
Demo seguro del sistema de búsqueda híbrida MINEDU
Implementa todas las medidas de seguridad gubernamentales
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import time
from datetime import datetime

# Agregar el directorio src al path
sys.path.append(str(Path(__file__).parent / "src"))

from core.config.security_config import SecurityConfig, SecurityError
from core.secure_search import SecureHybridSearch
from core.security.input_validator import InputValidator
from core.security.rate_limiter import RateLimiter
from core.security.privacy import PrivacyProtector
from core.security.monitor import SecurityMonitor
from core.security.logger import SecureLogger

class SecureRAGDemo:
    """
    Demo seguro del sistema RAG con todas las medidas de seguridad
    """
    
    def __init__(self):
        """Inicializar demo seguro"""
        self.security_config = SecurityConfig()
        self.input_validator = InputValidator()
        self.rate_limiter = RateLimiter()
        self.privacy_protector = PrivacyProtector()
        self.security_monitor = SecurityMonitor()
        self.secure_logger = SecureLogger()
        
        # Inicializar sistema de búsqueda seguro
        try:
            self.search_system = SecureHybridSearch()
            self.secure_logger.log_info("SecureRAGDemo initialized successfully")
        except Exception as e:
            self.secure_logger.log_error(f"Failed to initialize search system: {e}")
            raise SecurityError(f"Error inicializando sistema de búsqueda: {e}")
    
    def validate_query(self, query: str) -> bool:
        """
        Validar consulta del usuario con todas las medidas de seguridad
        
        Args:
            query: Consulta a validar
            
        Returns:
            bool: True si la consulta es válida
        """
        try:
            # Validar entrada básica
            if not self.input_validator.validate_text_input(query):
                self.secure_logger.log_warning("Query validation failed: invalid text input")
                return False
            
            # Sanitizar entrada
            sanitized_query = self.security_config.sanitize_input(query)
            if sanitized_query != query:
                self.secure_logger.log_info("Query sanitized for security")
            
            # Verificar rate limiting
            if not self.rate_limiter.check_rate_limit("query"):
                self.secure_logger.log_warning("Rate limit exceeded for query")
                return False
            
            # Verificar patrones peligrosos
            if self.input_validator.contains_dangerous_patterns(sanitized_query):
                self.secure_logger.log_warning("Query contains dangerous patterns")
                return False
            
            # Verificar longitud
            if len(sanitized_query) > self.security_config.MAX_QUERY_LENGTH:
                self.secure_logger.log_warning("Query too long")
                return False
            
            # Verificar contenido vacío
            if not sanitized_query.strip():
                self.secure_logger.log_warning("Empty query after sanitization")
                return False
            
            self.secure_logger.log_info("Query validation successful")
            return True
            
        except Exception as e:
            self.secure_logger.log_error(f"Query validation error: {e}")
            return False
    
    def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Realizar búsqueda segura
        
        Args:
            query: Consulta del usuario
            max_results: Número máximo de resultados
            
        Returns:
            Dict: Resultados de la búsqueda con metadatos de seguridad
        """
        start_time = time.time()
        
        try:
            # Validar consulta
            if not self.validate_query(query):
                return {
                    'success': False,
                    'error': 'Consulta no válida por razones de seguridad',
                    'security_events': self.security_monitor.get_recent_events()
                }
            
            # Sanitizar consulta
            sanitized_query = self.security_config.sanitize_input(query)
            
            # Proteger datos personales en la consulta
            protected_query = self.privacy_protector.protect_pii(sanitized_query)
            
            # Realizar búsqueda segura
            results = self.search_system.search(
                query=protected_query,
                max_results=min(max_results, self.security_config.MAX_RESULTS_PER_QUERY)
            )
            
            # Registrar evento de búsqueda exitosa
            self.security_monitor.log_search_event(
                query_length=len(sanitized_query),
                results_count=len(results.get('results', [])),
                execution_time=time.time() - start_time
            )
            
            # Preparar respuesta segura
            response = {
                'success': True,
                'query': sanitized_query,
                'results': results.get('results', []),
                'metadata': {
                    'execution_time': round(time.time() - start_time, 3),
                    'results_count': len(results.get('results', [])),
                    'security_version': self.security_config.SECURITY_VERSION,
                    'session_id': self.security_config.session_id,
                    'timestamp': datetime.now().isoformat()
                },
                'security_info': {
                    'query_sanitized': sanitized_query != query,
                    'pii_protected': protected_query != sanitized_query,
                    'rate_limit_status': self.rate_limiter.get_status(),
                    'security_events': self.security_monitor.get_recent_events()
                }
            }
            
            self.secure_logger.log_info(f"Search completed successfully: {len(results.get('results', []))} results")
            return response
            
        except Exception as e:
            self.secure_logger.log_error(f"Search error: {e}")
            return {
                'success': False,
                'error': f'Error en la búsqueda: {str(e)}',
                'security_events': self.security_monitor.get_recent_events()
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Obtener estado del sistema de seguridad
        
        Returns:
            Dict: Estado del sistema
        """
        return {
            'security_config': self.security_config.get_config_summary(),
            'rate_limiter_status': self.rate_limiter.get_status(),
            'security_monitor_status': self.security_monitor.get_status(),
            'recent_security_events': self.security_monitor.get_recent_events(),
            'system_health': 'OK'
        }
    
    def run_interactive_demo(self):
        """Ejecutar demo interactivo seguro"""
        print("🔒 SISTEMA DE BÚSQUEDA SEGURA MINEDU")
        print("=" * 50)
        print(f"Versión de seguridad: {self.security_config.SECURITY_VERSION}")
        print(f"ID de sesión: {self.security_config.session_id}")
        print("=" * 50)
        
        while True:
            try:
                print("\n📝 Ingrese su consulta (o 'salir' para terminar):")
                query = input("> ").strip()
                
                if query.lower() in ['salir', 'exit', 'quit']:
                    print("👋 ¡Hasta luego!")
                    break
                
                if not query:
                    print("❌ Por favor ingrese una consulta válida.")
                    continue
                
                print(f"\n🔍 Buscando: '{query}'")
                print("⏳ Procesando con medidas de seguridad...")
                
                results = self.search(query)
                
                if results['success']:
                    print(f"\n✅ Búsqueda completada en {results['metadata']['execution_time']}s")
                    print(f"📊 Resultados encontrados: {results['metadata']['results_count']}")
                    
                    if results['results']:
                        print("\n📋 RESULTADOS:")
                        for i, result in enumerate(results['results'][:3], 1):
                            print(f"\n{i}. {result.get('title', 'Sin título')}")
                            print(f"   📄 {result.get('source', 'Fuente desconocida')}")
                            print(f"   📝 {result.get('content', '')[:200]}...")
                    else:
                        print("❌ No se encontraron resultados relevantes.")
                    
                    # Mostrar información de seguridad si hubo eventos
                    if results['security_info']['security_events']:
                        print(f"\n🛡️ Eventos de seguridad: {len(results['security_info']['security_events'])}")
                
                else:
                    print(f"❌ Error: {results['error']}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Demo interrumpido por el usuario.")
                break
            except Exception as e:
                print(f"❌ Error inesperado: {e}")
                self.secure_logger.log_error(f"Interactive demo error: {e}")

def main():
    """Función principal del demo seguro"""
    if len(sys.argv) > 1:
        # Modo consulta directa
        query = " ".join(sys.argv[1:])
        
        try:
            demo = SecureRAGDemo()
            results = demo.search(query)
            
            if results['success']:
                print(f"✅ Búsqueda exitosa: {len(results['results'])} resultados")
                for i, result in enumerate(results['results'][:3], 1):
                    print(f"\n{i}. {result.get('title', 'Sin título')}")
                    print(f"   {result.get('content', '')[:200]}...")
            else:
                print(f"❌ Error: {results['error']}")
                
        except Exception as e:
            print(f"❌ Error del sistema: {e}")
            sys.exit(1)
    else:
        # Modo interactivo
        try:
            demo = SecureRAGDemo()
            demo.run_interactive_demo()
        except Exception as e:
            print(f"❌ Error inicializando demo: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main() 