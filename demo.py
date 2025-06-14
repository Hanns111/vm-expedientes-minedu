#!/usr/bin/env python3
"""
Demo Unificado del Sistema de Búsqueda Híbrido MINEDU
Combina funcionalidades de demo.py, demo_secure.py y demo_working.py

Uso:
  python demo.py "tu consulta"                    # Modo básico
  python demo.py --secure "tu consulta"           # Modo seguro completo
  python demo.py --interactive                    # Modo interactivo
  python demo.py --status                         # Estado del sistema
  python demo.py --help                           # Ayuda
"""

import sys
import os
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config.security_config import SecurityConfig, SecurityError
from src.core.secure_search import SecureHybridSearch

# Importaciones condicionales para modo seguro
try:
    from src.core.security.input_validator import InputValidator
    from src.core.security.rate_limiter import RateLimiter
    from src.core.security.privacy import PrivacyProtector
    from src.core.security.monitor import SecurityMonitor
    from src.core.security.logger import SecureLogger
    SECURE_MODE_AVAILABLE = True
except ImportError:
    SECURE_MODE_AVAILABLE = False

class UnifiedDemo:
    """
    Demo unificado del sistema RAG con múltiples modos de operación
    """
    
    def __init__(self, secure_mode: bool = False):
        """Inicializar demo unificado"""
        self.secure_mode = secure_mode and SECURE_MODE_AVAILABLE
        self.security_config = SecurityConfig()
        
        # Inicializar componentes de seguridad si está disponible
        if self.secure_mode:
            self.input_validator = InputValidator()
            self.rate_limiter = RateLimiter()
            self.privacy_protector = PrivacyProtector()
            self.security_monitor = SecurityMonitor()
            self.secure_logger = SecureLogger()
        
        # Inicializar sistema de búsqueda
        try:
            self.search_system = SecureHybridSearch()
            if self.secure_mode:
                self.secure_logger.log_info("UnifiedDemo initialized in secure mode")
            else:
                print("✅ Sistema de búsqueda inicializado en modo básico")
        except Exception as e:
            if self.secure_mode:
                self.secure_logger.log_error(f"Failed to initialize search system: {e}")
                raise SecurityError(f"Error inicializando sistema de búsqueda: {e}")
            else:
                raise Exception(f"Error inicializando sistema de búsqueda: {e}")
    
    def validate_query(self, query: str) -> bool:
        """
        Validar consulta del usuario
        
        Args:
            query: Consulta a validar
            
        Returns:
            bool: True si la consulta es válida
        """
        if not self.secure_mode:
            # Validación básica
            return bool(query and query.strip())
        
        try:
            # Validación completa de seguridad
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
            if self.secure_mode:
                self.secure_logger.log_error(f"Query validation error: {e}")
            return False
    
    def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Realizar búsqueda
        
        Args:
            query: Consulta del usuario
            max_results: Número máximo de resultados
            
        Returns:
            Dict: Resultados de la búsqueda
        """
        start_time = time.time()
        
        try:
            # Validar consulta
            if not self.validate_query(query):
                error_msg = 'Consulta no válida por razones de seguridad' if self.secure_mode else 'Consulta vacía o inválida'
                return {
                    'success': False,
                    'error': error_msg,
                    'security_events': self.security_monitor.get_recent_events() if self.secure_mode else []
                }
            
            # Sanitizar consulta
            if self.secure_mode:
                sanitized_query = self.security_config.sanitize_input(query)
                protected_query = self.privacy_protector.protect_pii(sanitized_query)
            else:
                sanitized_query = query
                protected_query = query
            
            # Realizar búsqueda
            results = self.search_system.search(
                query=protected_query,
                max_results=min(max_results, self.security_config.MAX_RESULTS_PER_QUERY)
            )
            
            # Registrar evento si está en modo seguro
            if self.secure_mode:
                self.security_monitor.log_search_event(
                    query_length=len(sanitized_query),
                    results_count=len(results.get('results', [])),
                    execution_time=time.time() - start_time
                )
            
            # Preparar respuesta
            response = {
                'success': True,
                'query': sanitized_query,
                'results': results.get('results', []),
                'metadata': {
                    'execution_time': round(time.time() - start_time, 3),
                    'results_count': len(results.get('results', [])),
                    'security_version': self.security_config.SECURITY_VERSION,
                    'session_id': self.security_config.session_id,
                    'timestamp': datetime.now().isoformat(),
                    'mode': 'secure' if self.secure_mode else 'basic'
                }
            }
            
            # Agregar información de seguridad si está disponible
            if self.secure_mode:
                response['security_info'] = {
                    'query_sanitized': sanitized_query != query,
                    'pii_protected': protected_query != sanitized_query,
                    'rate_limit_status': self.rate_limiter.get_status(),
                    'security_events': self.security_monitor.get_recent_events()
                }
            
            if self.secure_mode:
                self.secure_logger.log_info(f"Search completed successfully: {len(results.get('results', []))} results")
            
            return response
            
        except Exception as e:
            if self.secure_mode:
                self.secure_logger.log_error(f"Search error: {e}")
            return {
                'success': False,
                'error': f'Error en la búsqueda: {str(e)}',
                'security_events': self.security_monitor.get_recent_events() if self.secure_mode else []
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Obtener estado del sistema
        
        Returns:
            Dict: Estado del sistema
        """
        status = {
            'security_config': self.security_config.get_config_summary(),
            'system_health': 'OK',
            'mode': 'secure' if self.secure_mode else 'basic'
        }
        
        if self.secure_mode:
            status.update({
                'rate_limiter_status': self.rate_limiter.get_status(),
                'security_monitor_status': self.security_monitor.get_status(),
                'recent_security_events': self.security_monitor.get_recent_events()
            })
        
        return status
    
    def run_interactive_demo(self):
        """Ejecutar demo interactivo"""
        mode_text = "SEGURO" if self.secure_mode else "BÁSICO"
        print(f"🔒 SISTEMA DE BÚSQUEDA {mode_text} MINEDU")
        print("=" * 50)
        print(f"Versión de seguridad: {self.security_config.SECURITY_VERSION}")
        print(f"ID de sesión: {self.security_config.session_id}")
        print(f"Modo: {'Seguro' if self.secure_mode else 'Básico'}")
        print("=" * 50)
        
        # Mostrar consultas de ejemplo
        print("\n📝 Consultas de ejemplo:")
        example_queries = [
            "¿Cuál es el monto máximo diario para viáticos nacionales?",
            "¿Quién autoriza los viáticos en el MINEDU?",
            "¿Qué documentos se requieren para solicitar viáticos?",
            "¿Cuántos días antes debo solicitar viáticos?",
            "¿Cómo se rinden los gastos de viáticos?"
        ]
        
        for i, query in enumerate(example_queries, 1):
            print(f"  {i}. {query}")
        
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
                print("⏳ Procesando...")
                
                results = self.search(query)
                
                if results['success']:
                    print(f"\n✅ Búsqueda completada en {results['metadata']['execution_time']}s")
                    print(f"📊 Resultados encontrados: {results['metadata']['results_count']}")
                    
                    if results['results']:
                        print("\n📋 RESULTADOS:")
                        for i, result in enumerate(results['results'][:3], 1):
                            print(f"\n{i}. Score: {result.get('score', 0):.3f} | Método: {result.get('method', 'N/A')}")
                            print(f"   {result.get('text', '')[:200]}...")
                    else:
                        print("❌ No se encontraron resultados relevantes.")
                    
                    # Mostrar información de seguridad si está disponible
                    if self.secure_mode and 'security_info' in results:
                        security_info = results['security_info']
                        if security_info['security_events']:
                            print(f"\n🛡️ Eventos de seguridad: {len(security_info['security_events'])}")
                else:
                    print(f"❌ Error: {results['error']}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Demo interrumpido por el usuario.")
                break
            except Exception as e:
                print(f"❌ Error inesperado: {e}")

def main():
    """Función principal del demo unificado"""
    parser = argparse.ArgumentParser(
        description="Demo unificado del Sistema de Búsqueda Híbrido MINEDU",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python demo.py "¿Cuál es el monto máximo para viáticos?"
  python demo.py --secure "consulta con validación completa"
  python demo.py --interactive
  python demo.py --status
        """
    )
    
    parser.add_argument('query', nargs='?', help='Consulta a buscar')
    parser.add_argument('--secure', action='store_true', help='Modo seguro con todas las validaciones')
    parser.add_argument('--interactive', action='store_true', help='Modo interactivo')
    parser.add_argument('--status', action='store_true', help='Mostrar estado del sistema')
    parser.add_argument('--max-results', type=int, default=5, help='Número máximo de resultados')
    
    args = parser.parse_args()
    
    try:
        # Verificar modo seguro
        if args.secure and not SECURE_MODE_AVAILABLE:
            print("⚠️ ADVERTENCIA: Modo seguro no disponible. Ejecutando en modo básico.")
            print("💡 Para habilitar modo seguro, instale las dependencias de seguridad.")
            args.secure = False
        
        # Inicializar demo
        demo = UnifiedDemo(secure_mode=args.secure)
        
        # Ejecutar según argumentos
        if args.status:
            status = demo.get_system_status()
            print("📊 ESTADO DEL SISTEMA:")
            print("=" * 50)
            print(f"Modo: {status['mode']}")
            print(f"Versión: {status['security_config']['version']}")
            print(f"Salud: {status['system_health']}")
            print(f"ID de sesión: {status['security_config']['session_id']}")
            
            if args.secure:
                print(f"Rate limiter: {status['rate_limiter_status']}")
                print(f"Eventos de seguridad: {len(status['recent_security_events'])}")
        
        elif args.interactive:
            demo.run_interactive_demo()
        
        elif args.query:
            print(f"\n🔒 Búsqueda {'SEGURA' if args.secure else 'BÁSICA'}: {args.query}")
            print("-" * 50)
            
            results = demo.search(args.query, max_results=args.max_results)
            
            if results['success']:
                print(f"\n📊 Encontrados {len(results['results'])} resultados:\n")
                for i, result in enumerate(results['results'], 1):
                    print(f"{i}. Score: {result.get('score', 0):.3f} | Método: {result.get('method', 'N/A')}")
                    print(f"   {result.get('text', '')[:200]}...")
                    print()
                print("✅ Búsqueda completada exitosamente")
            else:
                print(f"\n❌ Error: {results['error']}")
        
        else:
            parser.print_help()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
