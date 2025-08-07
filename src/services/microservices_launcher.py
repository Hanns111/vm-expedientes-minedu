"""
Microservices Launcher - Lanzador de microservicios para Fase 5
Orquesta el inicio de todos los microservicios de la arquitectura distribuida
"""
import logging
import asyncio
import signal
import sys
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

# Importar todos los microservicios
from .gateway_service import GatewayService
from .rag_service import RAGService
from .agents_service import AgentsService
from .memory_service import MemoryService
from .calculation_service import CalculationService

logger = logging.getLogger(__name__)

class MicroservicesLauncher:
    """
    Lanzador de microservicios para arquitectura distribuida
    Maneja inicio, monitoreo y cierre graceful de todos los servicios
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        self.services = {}
        self.tasks = []
        self.shutdown_event = asyncio.Event()
        
        # Configurar logging
        self._setup_logging()
        
        logger.info(">> MicroservicesLauncher inicializado")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuración por defecto de microservicios"""
        return {
            "services": {
                "gateway": {
                    "class": GatewayService,
                    "port": 8000,
                    "enabled": True,
                    "priority": 1  # Se inicia al final para que los servicios estén listos
                },
                "rag": {
                    "class": RAGService,
                    "port": 8001,
                    "enabled": True,
                    "priority": 0
                },
                "agents": {
                    "class": AgentsService,
                    "port": 8002,
                    "enabled": True,
                    "priority": 0
                },
                "memory": {
                    "class": MemoryService,
                    "port": 8003,
                    "enabled": True,
                    "priority": 0
                },
                "calculation": {
                    "class": CalculationService,
                    "port": 8004,
                    "enabled": True,
                    "priority": 0
                }
            },
            "startup_delay": 2,  # Segundos entre inicios de servicios
            "health_check_interval": 30,  # Segundos
            "graceful_shutdown_timeout": 10  # Segundos
        }
    
    def _setup_logging(self):
        """Configurar logging para microservicios"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('microservices.log')
            ]
        )
    
    async def start_all_services(self):
        """Iniciar todos los microservicios"""
        try:
            logger.info("[LAUNCH] Iniciando arquitectura de microservicios - Fase 5: RAGP")
            
            # Configurar manejadores de señales
            self._setup_signal_handlers()
            
            # Ordenar servicios por prioridad
            services_config = self.config["services"]
            sorted_services = sorted(
                services_config.items(),
                key=lambda x: x[1]["priority"]
            )
            
            # Iniciar servicios en orden
            for service_name, service_config in sorted_services:
                if service_config["enabled"]:
                    await self._start_service(service_name, service_config)
                    
                    # Delay entre inicios
                    await asyncio.sleep(self.config["startup_delay"])
            
            # Iniciar monitoreo de salud
            health_task = asyncio.create_task(self._health_monitor())
            self.tasks.append(health_task)
            
            logger.info("[OK] Todos los microservicios iniciados correctamente")
            self._print_services_summary()
            
            # Esperar señal de cierre
            await self.shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"[ERROR] Error iniciando microservicios: {e}")
            raise
        finally:
            await self._shutdown_all_services()
    
    async def _start_service(self, service_name: str, service_config: Dict[str, Any]):
        """Iniciar un microservicio individual"""
        try:
            service_class = service_config["class"]
            port = service_config["port"]
            
            logger.info(f"[LAUNCH] Iniciando {service_name} en puerto {port}")
            
            # Crear instancia del servicio
            service_instance = service_class(port=port)
            self.services[service_name] = service_instance
            
            # Iniciar servicio en tarea asíncrona
            task = asyncio.create_task(
                service_instance.start_service(),
                name=f"{service_name}_service"
            )
            self.tasks.append(task)
            
            # Verificar que el servicio esté listo
            await self._wait_for_service_ready(service_name, service_instance)
            
            logger.info(f"[OK] {service_name} iniciado correctamente en puerto {port}")
            
        except Exception as e:
            logger.error(f"[ERROR] Error iniciando {service_name}: {e}")
            raise
    
    async def _wait_for_service_ready(self, service_name: str, service_instance):
        """Esperar a que un servicio esté listo"""
        max_attempts = 10
        attempt = 0
        
        while attempt < max_attempts:
            try:
                health_result = await service_instance.health_check()
                if health_result.get("status") == "healthy":
                    return
            except Exception as e:
                logger.debug(f"Health check fallido para {service_name}: {e}")
            
            attempt += 1
            await asyncio.sleep(1)
        
        logger.warning(f"[WARN] {service_name} no respondió a health check")
    
    async def _health_monitor(self):
        """Monitor de salud de microservicios"""
        while not self.shutdown_event.is_set():
            try:
                await asyncio.sleep(self.config["health_check_interval"])
                
                # Verificar salud de todos los servicios
                health_status = {}
                for service_name, service_instance in self.services.items():
                    try:
                        health_result = await service_instance.health_check()
                        health_status[service_name] = health_result.get("status", "unknown")
                    except Exception as e:
                        health_status[service_name] = "unhealthy"
                        logger.warning(f"[WARN] {service_name} health check fallido: {e}")
                
                # Log estado general
                healthy_count = sum(1 for status in health_status.values() if status == "healthy")
                total_count = len(health_status)
                
                logger.info(f"🟢 Health Status: {healthy_count}/{total_count} servicios saludables")
                
                if healthy_count < total_count:
                    unhealthy = [name for name, status in health_status.items() if status != "healthy"]
                    logger.warning(f"[WARN] Servicios no saludables: {unhealthy}")
                
            except Exception as e:
                logger.error(f"[ERROR] Error en monitor de salud: {e}")
    
    def _setup_signal_handlers(self):
        """Configurar manejadores de señales para cierre graceful"""
        def signal_handler(signum, frame):
            logger.info(f"[WARN] Señal {signum} recibida - iniciando cierre graceful")
            asyncio.create_task(self._trigger_shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _trigger_shutdown(self):
        """Activar cierre graceful"""
        self.shutdown_event.set()
    
    async def _shutdown_all_services(self):
        """Cierre graceful de todos los servicios"""
        logger.info("🛑 Iniciando cierre graceful de microservicios")
        
        try:
            # Cancelar todas las tareas
            for task in self.tasks:
                if not task.done():
                    task.cancel()
            
            # Esperar a que terminen las tareas
            if self.tasks:
                await asyncio.wait(
                    self.tasks,
                    timeout=self.config["graceful_shutdown_timeout"],
                    return_when=asyncio.ALL_COMPLETED
                )
            
            logger.info("[OK] Todos los microservicios cerrados correctamente")
            
        except Exception as e:
            logger.error(f"[ERROR] Error durante cierre: {e}")
    
    def _print_services_summary(self):
        """Imprimir resumen de servicios iniciados"""
        print("\n" + "=" * 60)
        print("🎆 FASE 5: RAGP - RAG PRODUCTIVO EMPRESARIAL")
        print("Arquitectura de Microservicios Iniciada")
        print("=" * 60)
        
        for service_name, service_config in self.config["services"].items():
            if service_config["enabled"]:
                port = service_config["port"]
                print(f"🟢 {service_name.upper():<12} -> http://localhost:{port}")
        
        print("\n🎯 Endpoints principales:")
        print(f"🌐 Gateway API    -> http://localhost:8000")
        print(f"📈 Health Checks  -> http://localhost:8000/health")
        print(f"[STATS] Métricas       -> http://localhost:8000/metrics")
        print("\n⚡ Sistema listo para recibir consultas")
        print("=" * 60 + "\n")
    
    def get_services_status(self) -> Dict[str, Any]:
        """Obtener estado de todos los servicios"""
        return {
            "launcher_status": "running" if not self.shutdown_event.is_set() else "shutdown",
            "services_count": len(self.services),
            "tasks_count": len(self.tasks),
            "services": list(self.services.keys()),
            "timestamp": datetime.now().isoformat()
        }

# Función principal para lanzar microservicios
async def launch_microservices(config: Dict[str, Any] = None):
    """Función principal para lanzar todos los microservicios"""
    launcher = MicroservicesLauncher(config)
    await launcher.start_all_services()

if __name__ == "__main__":
    # Ejecutar launcher directamente
    asyncio.run(launch_microservices())
