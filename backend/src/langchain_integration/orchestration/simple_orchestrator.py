"""
Orquestador simple que simula LangGraph sin dependencias
Implementa routing básico a agentes especializados
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from ..agents.viaticos_agent import viaticos_agent
from ..config import config

logger = logging.getLogger(__name__)

class SimpleOrchestrator:
    """Orquestador simple para sistema RAG multiagente"""
    
    def __init__(self):
        self.orchestrator_name = "simple_orchestrator"
        
        # Registro de agentes disponibles
        self.agents = {
            "viaticos": viaticos_agent,
            # Aquí se agregarán más agentes en el futuro
            # "igv": igv_agent,
            # "renta": renta_agent,
        }
        
        # Patterns para detección de intención
        self.intent_patterns = {
            "viaticos": [
                "viático", "viaticos", "viáticos", 
                "monto", "gastos", "comisión", "comision",
                "declaración jurada", "declaracion jurada",
                "provincia", "lima", "diario", "máximo", "maximo"
            ],
            "igv": [
                "igv", "impuesto", "ventas", "tasa", "alicuota"
            ],
            "renta": [
                "renta", "cuarta categoria", "quinta categoria", "retención", "retencion"
            ],
            "general": []
        }
    
    def analyze_intent(self, query: str) -> Dict[str, Any]:
        """Analizar intención de la consulta para routing"""
        query_lower = query.lower()
        
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            matched_patterns = []
            
            for pattern in patterns:
                if pattern in query_lower:
                    score += len(pattern)  # Patrones más largos valen más
                    matched_patterns.append(pattern)
            
            if score > 0:
                intent_scores[intent] = {
                    "score": score,
                    "patterns": matched_patterns
                }
        
        # Determinar intención principal
        if intent_scores:
            primary_intent = max(intent_scores.keys(), key=lambda x: intent_scores[x]["score"])
            confidence = min(intent_scores[primary_intent]["score"] / 10, 1.0)
        else:
            primary_intent = "general"
            confidence = 0.3
        
        return {
            "primary_intent": primary_intent,
            "confidence": confidence,
            "all_scores": intent_scores,
            "query": query
        }
    
    def route_to_agent(self, intent_analysis: Dict[str, Any]) -> str:
        """Determinar qué agente debe procesar la consulta"""
        primary_intent = intent_analysis["primary_intent"]
        confidence = intent_analysis["confidence"]
        
        # Si la confianza es muy baja, usar agente general (viáticos por defecto)
        if confidence < 0.4:
            return "viaticos"  # Agente por defecto
        
        # Routing basado en intención
        if primary_intent in self.agents:
            return primary_intent
        else:
            return "viaticos"  # Fallback al agente viáticos
    
    async def execute_agent(self, agent_name: str, query: str) -> Dict[str, Any]:
        """Ejecutar agente específico"""
        try:
            if agent_name not in self.agents:
                raise ValueError(f"Agente '{agent_name}' no disponible")
            
            agent = self.agents[agent_name]
            
            # Ejecutar agente
            if hasattr(agent, 'process_query'):
                result = await agent.process_query(query)
            else:
                # Fallback para agentes sin método async
                result = {
                    "response": f"Agente {agent_name} procesó: {query}",
                    "agent": agent_name,
                    "sources": [],
                    "confidence": 0.5
                }
            
            # Asegurar que el resultado tenga los campos necesarios
            result["agent_used"] = agent_name
            result["orchestrator"] = self.orchestrator_name
            
            return result
            
        except Exception as e:
            logger.error(f"Error ejecutando agente {agent_name}: {e}")
            return {
                "response": f"Error procesando con agente {agent_name}: {str(e)}",
                "agent_used": agent_name,
                "error": str(e),
                "sources": [],
                "confidence": 0.0
            }
    
    def synthesize_response(self, agent_results: List[Dict[str, Any]], 
                          intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Sintetizar respuesta final de uno o múltiples agentes"""
        
        if not agent_results:
            return {
                "response": "No se pudo procesar la consulta. Intenta reformular tu pregunta.",
                "sources": [],
                "confidence": 0.0,
                "agents_used": [],
                "synthesis_method": "empty_fallback"
            }
        
        # Para esta versión simple, usar el resultado del primer agente
        primary_result = agent_results[0]
        
        # Si hay múltiples agentes (futuro), aquí se fusionarían las respuestas
        if len(agent_results) > 1:
            # TODO: Implementar fusión inteligente de múltiples agentes
            logger.info(f"Múltiples agentes ejecutados: {len(agent_results)}")
        
        # Agregar metadatos de síntesis
        primary_result["synthesis_info"] = {
            "primary_intent": intent_analysis["primary_intent"],
            "intent_confidence": intent_analysis["confidence"],
            "agents_executed": len(agent_results),
            "synthesis_method": "single_agent" if len(agent_results) == 1 else "multi_agent"
        }
        
        return primary_result
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Procesar consulta completa usando orquestación"""
        start_time = datetime.now()
        
        try:
            logger.info(f"Orquestador procesando query: {query[:50]}...")
            
            # 1. Analizar intención
            intent_analysis = self.analyze_intent(query)
            logger.info(f"Intent detectado: {intent_analysis['primary_intent']} "
                       f"(confianza: {intent_analysis['confidence']:.2f})")
            
            # 2. Determinar agente(s) a ejecutar
            primary_agent = self.route_to_agent(intent_analysis)
            logger.info(f"Routing a agente: {primary_agent}")
            
            # 3. Ejecutar agente(s)
            agent_results = []
            
            # Ejecutar agente principal
            try:
                result = await self.execute_agent(primary_agent, query)
                agent_results.append(result)
            except Exception as e:
                logger.error(f"Error ejecutando agente principal: {e}")
                # Crear resultado de error
                agent_results.append({
                    "response": f"Error en agente {primary_agent}: {str(e)}",
                    "agent_used": primary_agent,
                    "error": str(e),
                    "sources": [],
                    "confidence": 0.0
                })
            
            # TODO: En futuras versiones, ejecutar agentes secundarios si es necesario
            
            # 4. Sintetizar respuesta final
            final_result = self.synthesize_response(agent_results, intent_analysis)
            
            # 5. Agregar metadatos del orquestador
            processing_time = (datetime.now() - start_time).total_seconds()
            
            final_result.update({
                "orchestrator_info": {
                    "orchestrator": self.orchestrator_name,
                    "total_processing_time": round(processing_time, 3),
                    "timestamp": datetime.now().isoformat(),
                    "agents_available": list(self.agents.keys()),
                    "routing_decision": primary_agent
                }
            })
            
            logger.info(f"Orquestador completado en {processing_time:.3f}s")
            return final_result
            
        except Exception as e:
            logger.error(f"Error en orquestador: {e}")
            return {
                "response": f"Error en orquestación: {str(e)}",
                "sources": [],
                "confidence": 0.0,
                "error": str(e),
                "orchestrator_info": {
                    "orchestrator": self.orchestrator_name,
                    "error": True,
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado del sistema"""
        try:
            # Verificar estado de agentes
            agent_status = {}
            for agent_name, agent in self.agents.items():
                agent_status[agent_name] = {
                    "available": True,
                    "type": type(agent).__name__
                }
            
            # Estadísticas del retriever
            from ..vectorstores.simple_retriever import retriever
            retriever_stats = retriever.get_stats()
            
            return {
                "orchestrator": self.orchestrator_name,
                "status": "operational",
                "agents": agent_status,
                "retriever_stats": retriever_stats,
                "config": config.to_dict(),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado del sistema: {e}")
            return {
                "orchestrator": self.orchestrator_name,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Instancia global
orchestrator = SimpleOrchestrator()