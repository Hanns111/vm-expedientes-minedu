"""
Router de agentes - Fase 4
Dirige consultas al agente apropiado
"""
import logging
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class AgentType(Enum):
    """Tipos de agentes disponibles"""
    CALCULATION = "calculation"
    LEGAL = "legal_expert"
    PROCEDURE = "procedure"
    HISTORICAL = "historical"
    QUERY_CLASSIFIER = "query_classifier"

class AgentRouter:
    """
    Router que dirige consultas al agente apropiado
    """
    
    def __init__(self):
        self.available_agents = {
            AgentType.CALCULATION: "CalculationAgent",
            AgentType.LEGAL: "LegalExpertAgent", 
            AgentType.PROCEDURE: "ProcedureAgent",
            AgentType.HISTORICAL: "HistoricalAgent",
            AgentType.QUERY_CLASSIFIER: "QueryClassifierAgent"
        }
        logger.info("🎯 AgentRouter inicializado")
    
    def route_query(self, query: str, suggested_agent: Optional[AgentType] = None) -> AgentType:
        """
        Determinar qué agente debe manejar la consulta
        """
        if suggested_agent and suggested_agent in self.available_agents:
            return suggested_agent
            
        # Lógica básica de routing
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['monto', 'cálculo', 'viático', 'suma']):
            return AgentType.CALCULATION
        elif any(word in query_lower for word in ['legal', 'normativa', 'artículo']):
            return AgentType.LEGAL
        elif any(word in query_lower for word in ['procedimiento', 'trámite', 'proceso']):
            return AgentType.PROCEDURE
        elif any(word in query_lower for word in ['histórico', 'precedente', 'anterior']):
            return AgentType.HISTORICAL
        else:
            return AgentType.QUERY_CLASSIFIER
    
    def get_available_agents(self) -> Dict[str, str]:
        """Obtener agentes disponibles"""
        return {agent.value: name for agent, name in self.available_agents.items()}
    
    def get_router_stats(self) -> Dict[str, Any]:
        """Estadísticas del router"""
        return {
            "total_agents": len(self.available_agents),
            "available_agents": list(self.available_agents.keys()),
            "status": "active"
        } 