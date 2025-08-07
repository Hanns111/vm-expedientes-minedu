"""
LangGraph REAL Implementation - No más simuladores
Implementación completa con StateGraph, MessageState, y CompiledGraph
"""
import logging
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from datetime import datetime
import operator

# LangGraph REAL imports
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage

from ..agents.viaticos_agent import viaticos_agent
from ..config import config

logger = logging.getLogger(__name__)

# === REAL LANGGRAPH STATE ===
class RAGState(TypedDict):
    """Estado real de LangGraph para RAG multiagente"""
    messages: Annotated[List, add_messages]
    query: str
    intent: str
    confidence: float
    agent_used: str
    documents_found: int
    extracted_info: Dict[str, Any]
    sources: List[Dict[str, Any]]
    processing_time: float
    timestamp: str
    routing_decision: str

class RealLangGraphOrchestrator:
    """Orquestador LangGraph REAL - StateGraph con checkpointing"""
    
    def __init__(self):
        self.orchestrator_name = "real_langgraph"
        
        # Registro de agentes disponibles
        self.agents = {
            "viaticos": viaticos_agent,
            # Futuro: más agentes reales
        }
        
        # Patterns para routing inteligente
        self.intent_patterns = {
            "viaticos": [
                "viático", "viaticos", "viáticos", 
                "monto", "gastos", "comisión", "comision",
                "declaración jurada", "declaracion jurada",
                "provincia", "lima", "diario", "máximo", "maximo"
            ],
            "igv": ["igv", "impuesto", "ventas", "tasa", "alicuota"],
            "renta": ["renta", "cuarta categoria", "quinta categoria", "retención", "retencion"],
        }
        
        # Crear el StateGraph REAL
        self.workflow = self._build_real_stategraph()
        
        # Memory saver para checkpointing
        self.memory = MemorySaver()
        
        # Compilar el graph REAL
        self.compiled_graph = self.workflow.compile(checkpointer=self.memory)
        
        logger.info("🚀 LangGraph REAL inicializado con StateGraph y checkpointing")
    
    def _build_real_stategraph(self) -> StateGraph:
        """Construir StateGraph REAL de LangGraph"""
        
        # Crear workflow StateGraph
        workflow = StateGraph(RAGState)
        
        # === NODOS REALES ===
        workflow.add_node("analyze_intent", self._analyze_intent_node)
        workflow.add_node("route_to_agent", self._route_to_agent_node)
        workflow.add_node("viaticos_agent", self._viaticos_agent_node)
        workflow.add_node("synthesize_response", self._synthesize_response_node)
        
        # === EDGES REALES ===
        workflow.add_edge(START, "analyze_intent")
        workflow.add_edge("analyze_intent", "route_to_agent")
        
        # Conditional routing basado en intención
        workflow.add_conditional_edges(
            "route_to_agent",
            self._route_decision,
            {
                "viaticos": "viaticos_agent",
                "general": "viaticos_agent",  # Default por ahora
            }
        )
        
        workflow.add_edge("viaticos_agent", "synthesize_response")
        workflow.add_edge("synthesize_response", END)
        
        return workflow
    
    # === NODOS REALES DE LANGGRAPH ===
    
    async def _analyze_intent_node(self, state: RAGState) -> RAGState:
        """Nodo real para análisis de intención"""
        logger.info(f"🧠 [REAL LANGGRAPH] Analizando intención: {state['query'][:50]}...")
        
        query_lower = state["query"].lower()
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern in query_lower:
                    score += len(pattern)
            
            if score > 0:
                intent_scores[intent] = score
        
        if intent_scores:
            primary_intent = max(intent_scores.keys(), key=lambda x: intent_scores[x])
            confidence = min(intent_scores[primary_intent] / 10, 1.0)
        else:
            primary_intent = "general"
            confidence = 0.3
        
        # Actualizar estado
        state["intent"] = primary_intent
        state["confidence"] = confidence
        
        logger.info(f"✅ [REAL LANGGRAPH] Intent: {primary_intent} (confianza: {confidence:.2f})")
        
        return state
    
    async def _route_to_agent_node(self, state: RAGState) -> RAGState:
        """Nodo real para routing a agentes"""
        intent = state["intent"]
        confidence = state["confidence"]
        
        # Routing logic
        if confidence < 0.4 or intent not in self.agents:
            routing_decision = "viaticos"  # Default agent
        else:
            routing_decision = intent
        
        state["routing_decision"] = routing_decision
        
        logger.info(f"🚦 [REAL LANGGRAPH] Routing: {state['query'][:30]}... → {routing_decision}")
        
        return state
    
    async def _viaticos_agent_node(self, state: RAGState) -> RAGState:
        """Nodo real del agente de viáticos"""
        logger.info(f"🏛️ [REAL LANGGRAPH] Ejecutando agente viáticos...")
        
        try:
            # Ejecutar agente real
            agent_result = await viaticos_agent.process_query(state["query"])
            
            # Actualizar estado con resultados reales
            state["agent_used"] = "viaticos"
            state["documents_found"] = agent_result.get("documents_found", 0)
            state["extracted_info"] = agent_result.get("extracted_info", {})
            state["sources"] = agent_result.get("sources", [])
            state["processing_time"] = agent_result.get("processing_time", 0)
            
            # Agregar mensaje AI al estado
            response_text = agent_result.get("response", "")
            ai_message = AIMessage(content=response_text)
            state["messages"].append(ai_message)
            
            logger.info(f"✅ [REAL LANGGRAPH] Agente viáticos completado: {len(response_text)} chars")
            
        except Exception as e:
            logger.error(f"❌ [REAL LANGGRAPH] Error en agente viáticos: {e}")
            
            # Error handling en estado
            error_message = AIMessage(content=f"Error procesando consulta: {str(e)}")
            state["messages"].append(error_message)
            state["documents_found"] = 0
            state["extracted_info"] = {"error": str(e)}
        
        return state
    
    async def _synthesize_response_node(self, state: RAGState) -> RAGState:
        """Nodo real para síntesis de respuesta final"""
        logger.info(f"🔄 [REAL LANGGRAPH] Sintetizando respuesta final...")
        
        # Obtener última respuesta AI
        last_message = state["messages"][-1] if state["messages"] else None
        
        if last_message and isinstance(last_message, AIMessage):
            response_content = last_message.content
        else:
            response_content = "No se pudo procesar la consulta."
        
        # Agregar metadatos finales
        state["timestamp"] = datetime.now().isoformat()
        
        logger.info(f"✅ [REAL LANGGRAPH] Síntesis completada: {len(response_content)} chars")
        
        return state
    
    def _route_decision(self, state: RAGState) -> str:
        """Función de decisión para conditional edges"""
        routing_decision = state.get("routing_decision", "viaticos")
        logger.info(f"🎯 [REAL LANGGRAPH] Decisión de routing: {routing_decision}")
        return routing_decision
    
    # === API PRINCIPAL ===
    
    async def process_query_real(self, query: str, thread_id: str = None) -> Dict[str, Any]:
        """Procesar consulta con LangGraph REAL"""
        start_time = datetime.now()
        
        if not thread_id:
            thread_id = f"thread_{int(datetime.now().timestamp())}"
        
        try:
            logger.info(f"🚀 [REAL LANGGRAPH] Procesando query: {query[:50]}...")
            
            # Estado inicial REAL
            initial_state = {
                "messages": [HumanMessage(content=query)],
                "query": query,
                "intent": "",
                "confidence": 0.0,
                "agent_used": "",
                "documents_found": 0,
                "extracted_info": {},
                "sources": [],
                "processing_time": 0.0,
                "timestamp": "",
                "routing_decision": ""
            }
            
            # Configuración de thread para checkpointing
            config_thread = {"configurable": {"thread_id": thread_id}}
            
            # ¡EJECUTAR LANGGRAPH REAL!
            final_state = await self.compiled_graph.ainvoke(
                initial_state, 
                config=config_thread
            )
            
            # Calcular tiempo total
            total_time = (datetime.now() - start_time).total_seconds()
            
            # Extraer respuesta final
            last_message = final_state["messages"][-1]
            response_text = last_message.content if hasattr(last_message, 'content') else str(last_message)
            
            # Resultado final
            result = {
                "response": response_text,
                "sources": final_state.get("sources", []),
                "confidence": final_state.get("confidence", 0.0),
                "documents_found": final_state.get("documents_found", 0),
                "intent": final_state.get("intent", ""),
                "extracted_info": final_state.get("extracted_info", {}),
                "processing_time": round(total_time, 3),
                "method": "real_langgraph",
                "agent_used": final_state.get("agent_used", ""),
                "orchestrator_info": {
                    "orchestrator": self.orchestrator_name,
                    "thread_id": thread_id,
                    "total_processing_time": round(total_time, 3),
                    "timestamp": datetime.now().isoformat(),
                    "routing_decision": final_state.get("routing_decision", ""),
                    "langgraph_real": True
                }
            }
            
            logger.info(f"✅ [REAL LANGGRAPH] Completado en {total_time:.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ [REAL LANGGRAPH] Error: {e}")
            return {
                "response": f"Error en LangGraph real: {str(e)}",
                "sources": [],
                "confidence": 0.0,
                "error": str(e),
                "method": "real_langgraph_error",
                "orchestrator_info": {
                    "orchestrator": self.orchestrator_name,
                    "error": True,
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    def get_graph_visualization(self) -> str:
        """Obtener visualización del graph real"""
        try:
            # LangGraph real puede generar visualizaciones
            return self.compiled_graph.get_graph().draw_mermaid()
        except Exception as e:
            return f"Error generando visualización: {e}"
    
    def get_system_status(self) -> Dict[str, Any]:
        """Estado del sistema LangGraph real"""
        try:
            return {
                "orchestrator": self.orchestrator_name,
                "status": "real_langgraph_operational",
                "langgraph_version": "real",
                "agents": {name: {"available": True, "type": type(agent).__name__} 
                          for name, agent in self.agents.items()},
                "graph_nodes": list(self.workflow.nodes.keys()) if hasattr(self.workflow, 'nodes') else [],
                "checkpointing": True,
                "memory_saver": True,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "orchestrator": self.orchestrator_name,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Instancia global REAL
real_orchestrator = RealLangGraphOrchestrator()