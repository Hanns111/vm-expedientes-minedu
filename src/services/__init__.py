"""
Arquitectura de Microservicios - Fase 5: RAGP
RAG Productivo Empresarial con servicios distribuidos
Optimizado con lazy loading para evitar carga pesada
"""

# Funciones de lazy loading para evitar carga automática pesada
def get_gateway_service():
    """Lazy load Gateway Service"""
    from .gateway_service import GatewayService
    return GatewayService

def get_rag_service():
    """Lazy load RAG Service"""
    from .rag_service import get_rag_service
    return get_rag_service()

def get_agents_service():
    """Lazy load Agents Service"""
    from .agents_service import AgentsService
    return AgentsService

def get_memory_service():
    """Lazy load Memory Service"""
    from .memory_service import MemoryService
    return MemoryService

def get_calculation_service():
    """Lazy load Calculation Service"""
    from .calculation_service import CalculationService
    return CalculationService

__all__ = [
    'get_gateway_service',
    'get_rag_service',
    'get_agents_service',
    'get_memory_service',
    'get_calculation_service'
]