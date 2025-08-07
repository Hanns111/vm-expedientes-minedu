"""
Orquestador LangGraph para RAG Contextual Inteligente
Implementa StateGraph con agentes especializados y memoria episódica
"""
import logging
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from datetime import datetime
import json
import asyncio

try:
    from langgraph.graph import StateGraph, END
    from langgraph.graph.message import add_messages
    from langgraph.checkpoint.memory import MemorySaver
    from langchain.schema import BaseMessage, HumanMessage, AIMessage
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

# Agentes especializados
from ..agents.query_classifier import QueryClassifierAgent, QueryType
from ..agents.calculation_agent import CalculationAgent
from ..langchain_integration.semantic_rag import SemanticRAGChain

# Memoria episódica
from ..memory.episodic_memory import EpisodicMemoryManager

logger = logging.getLogger(__name__)

class RAGState(TypedDict):
    """Estado del grafo LangGraph para RAG contextual"""
    messages: Annotated[List[BaseMessage], add_messages]
    query: str
    query_type: str
    agent_route: str
    context_enhanced: bool
    episodic_context: Dict[str, Any]
    calculation_result: Optional[Dict[str, Any]]
    rag_result: Optional[Dict[str, Any]]
    final_response: str
    confidence: float
    reasoning_chain: List[str]
    metadata: Dict[str, Any]

class LangGraphOrchestrator:
    """
    Orquestador principal usando LangGraph para RAG contextual inteligente
    Coordina agentes especializados con memoria episódica
    """
    
    def __init__(self):
        # Verificar disponibilidad de LangGraph
        if not LANGGRAPH_AVAILABLE:
            logger.warning("⚠️ LangGraph no disponible - usando implementación simulada")
        
        # Inicializar agentes especializados
        self.query_classifier = QueryClassifierAgent()
        self.calculation_agent = CalculationAgent()
        self.semantic_rag = SemanticRAGChain()
        
        # Memoria episódica
        self.episodic_memory = EpisodicMemoryManager()
        
        # Construir grafo LangGraph
        self.graph = self._build_langgraph()
        
        # Configurar memoria persistente
        self.memory = MemorySaver() if LANGGRAPH_AVAILABLE else None
        
        # Compilar grafo
        self.compiled_graph = self._compile_graph()
        
        logger.info("🎯 LangGraphOrchestrator inicializado con memoria episódica")
    
    def _build_langgraph(self) -> StateGraph:
        """Construir el grafo LangGraph con nodos especializados"""
        
        if not LANGGRAPH_AVAILABLE:
            return None
        
        # Crear grafo de estado
        workflow = StateGraph(RAGState)
        
        # Añadir nodos especializados
        workflow.add_node("classify_query", self._classify_query_node)
        workflow.add_node("retrieve_episodic", self._retrieve_episodic_node)
        workflow.add_node("route_to_agent", self._route_to_agent_node)
        workflow.add_node("calculation_agent", self._calculation_agent_node)
        workflow.add_node("semantic_rag_agent", self._semantic_rag_node)
        workflow.add_node("context_enhancer", self._context_enhancer_node)
        workflow.add_node("response_synthesizer", self._response_synthesizer_node)
        workflow.add_node("episodic_recorder", self._episodic_recorder_node)
        
        # Definir punto de entrada
        workflow.set_entry_point("classify_query")
        
        # Definir flujo condicional
        workflow.add_conditional_edges(
            "classify_query",
            self._determine_next_step,
            {
                "retrieve_episodic": "retrieve_episodic",
                "route_to_agent": "route_to_agent"
            }
        )
        
        workflow.add_edge("retrieve_episodic", "route_to_agent")
        
        workflow.add_conditional_edges(
            "route_to_agent",
            self._route_agent_decision,
            {
                "calculation": "calculation_agent",
                "semantic_rag": "semantic_rag_agent",
                "context_enhance": "context_enhancer"
            }
        )
        
        workflow.add_edge("calculation_agent", "context_enhancer")
        workflow.add_edge("semantic_rag_agent", "context_enhancer")
        workflow.add_edge("context_enhancer", "response_synthesizer")
        workflow.add_edge("response_synthesizer", "episodic_recorder")
        workflow.add_edge("episodic_recorder", END)
        
        return workflow
    
    def _compile_graph(self):
        """Compilar el grafo con memoria"""
        if not LANGGRAPH_AVAILABLE or not self.graph:
            return None
        
        return self.graph.compile(checkpointer=self.memory)
    
    async def process_query(self, 
                          query: str, 
                          session_id: str = "default",
                          context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Procesar consulta usando LangGraph con agentes especializados
        
        Args:
            query: Consulta del usuario
            session_id: ID de sesión para memoria persistente
            context: Contexto adicional
            
        Returns:
            Respuesta procesada con reasoning chain completo
        """
        try:
            if not LANGGRAPH_AVAILABLE or not self.compiled_graph:
                # Fallback sin LangGraph
                return await self._process_query_fallback(query, context)
            
            # Estado inicial
            initial_state: RAGState = {
                "messages": [HumanMessage(content=query)],
                "query": query,
                "query_type": "",
                "agent_route": "",
                "context_enhanced": False,
                "episodic_context": {},
                "calculation_result": None,
                "rag_result": None,
                "final_response": "",
                "confidence": 0.0,
                "reasoning_chain": [],
                "metadata": {
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "context": context or {}
                }
            }
            
            # Configuración de ejecución
            config = {"configurable": {"thread_id": session_id}}
            
            # Ejecutar grafo
            final_state = await self.compiled_graph.ainvoke(initial_state, config)
            
            # Preparar respuesta
            response = {
                "answer": final_state["final_response"],
                "confidence": final_state["confidence"],
                "query_type": final_state["query_type"],
                "agent_used": final_state["agent_route"],
                "reasoning_chain": final_state["reasoning_chain"],
                "episodic_context": final_state["episodic_context"],
                "calculation_result": final_state["calculation_result"],
                "rag_result": final_state["rag_result"],
                "method": "langgraph_orchestrator",
                "session_id": session_id,
                "metadata": final_state["metadata"]
            }
            
            logger.info(f"🎯 Query procesada: {final_state['query_type']} via {final_state['agent_route']}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Error en LangGraph orchestrator: {e}")
            return await self._process_query_fallback(query, context)
    
    async def _classify_query_node(self, state: RAGState) -> RAGState:
        """Nodo: Clasificar consulta y determinar estrategia"""
        try:
            classification = self.query_classifier.classify_query(state["query"])
            
            state["query_type"] = classification.query_type.value
            state["agent_route"] = classification.target_agent
            state["confidence"] = classification.confidence
            
            state["reasoning_chain"].append(f"Clasificación: {classification.reasoning}")
            
            logger.info(f"🎯 Query clasificada: {classification.query_type.value}")
            return state
            
        except Exception as e:
            logger.error(f"❌ Error en clasificación: {e}")
            state["query_type"] = "general"
            state["agent_route"] = "semantic_rag_agent"
            return state
    
    async def _retrieve_episodic_node(self, state: RAGState) -> RAGState:
        """Nodo: Recuperar contexto episódico relevante"""
        try:
            session_id = state["metadata"]["session_id"]
            
            # Recuperar memoria episódica
            episodic_context = await self.episodic_memory.retrieve_relevant_episodes(
                query=state["query"],
                session_id=session_id,
                max_episodes=5
            )
            
            state["episodic_context"] = episodic_context
            
            if episodic_context.get("episodes"):
                context_summary = f"Contexto episódico: {len(episodic_context['episodes'])} episodios relevantes"
                state["reasoning_chain"].append(context_summary)
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error recuperando memoria episódica: {e}")
            state["episodic_context"] = {}
            return state
    
    async def _route_to_agent_node(self, state: RAGState) -> RAGState:
        """Nodo: Determinar routing a agente especializado"""
        
        # El routing ya fue determinado en classify_query
        reasoning = f"Routing: {state['agent_route']} para {state['query_type']}"
        state["reasoning_chain"].append(reasoning)
        
        return state
    
    async def _calculation_agent_node(self, state: RAGState) -> RAGState:
        """Nodo: Ejecutar agente de cálculos"""
        try:
            calculation_result = self.calculation_agent.process_calculation_query(
                query=state["query"],
                context=state["metadata"]["context"]
            )
            
            state["calculation_result"] = {
                "type": calculation_result.calculation_type,
                "value": str(calculation_result.result_value),
                "formatted": calculation_result.result_formatted,
                "legal_basis": calculation_result.legal_basis,
                "steps": calculation_result.calculation_steps,
                "confidence": calculation_result.confidence
            }
            
            reasoning = f"Cálculo completado: {calculation_result.result_formatted}"
            state["reasoning_chain"].append(reasoning)
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error en calculation agent: {e}")
            state["calculation_result"] = {"error": str(e)}
            return state
    
    async def _semantic_rag_node(self, state: RAGState) -> RAGState:
        """Nodo: Ejecutar RAG semántico"""
        try:
            rag_result = self.semantic_rag.search_and_generate(
                query=state["query"],
                max_docs=5
            )
            
            state["rag_result"] = rag_result
            
            reasoning = f"RAG: {len(rag_result.get('sources', []))} fuentes encontradas"
            state["reasoning_chain"].append(reasoning)
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error en semantic RAG: {e}")
            state["rag_result"] = {"error": str(e)}
            return state
    
    async def _context_enhancer_node(self, state: RAGState) -> RAGState:
        """Nodo: Mejorar contexto con información episódica"""
        try:
            # Combinar contexto episódico con resultados actuales
            enhanced_context = {}
            
            # Añadir contexto episódico relevante
            if state["episodic_context"].get("episodes"):
                enhanced_context["previous_interactions"] = state["episodic_context"]["episodes"]
            
            # Añadir resultados de cálculos si existen
            if state["calculation_result"]:
                enhanced_context["calculation_context"] = state["calculation_result"]
            
            # Añadir resultados RAG si existen
            if state["rag_result"]:
                enhanced_context["rag_context"] = state["rag_result"]
            
            state["context_enhanced"] = True
            state["reasoning_chain"].append("Contexto mejorado con memoria episódica")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error mejorando contexto: {e}")
            state["context_enhanced"] = False
            return state
    
    async def _response_synthesizer_node(self, state: RAGState) -> RAGState:
        """Nodo: Sintetizar respuesta final"""
        try:
            # Construir respuesta basada en tipo de consulta y resultados
            if state["calculation_result"] and not state["calculation_result"].get("error"):
                # Respuesta de cálculo
                calc = state["calculation_result"]
                response = f"""Según el cálculo realizado: {calc['formatted']}

**Base legal:** {calc['legal_basis']}

**Pasos del cálculo:**
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(calc['steps']))}

Esta información se basa en la normativa vigente del Ministerio de Educación."""
                
                state["confidence"] = calc["confidence"]
            
            elif state["rag_result"] and not state["rag_result"].get("error"):
                # Respuesta RAG
                rag = state["rag_result"]
                response = rag["answer"]
                
                if rag.get("sources"):
                    response += f"\n\n**Fuentes consultadas:** {len(rag['sources'])} documentos normativos"
                
                state["confidence"] = rag.get("confidence", 0.7)
            
            else:
                # Respuesta general
                response = f"""Basándome en la consulta "{state['query']}", la información disponible sugiere consultar la normativa específica aplicable.

Para obtener información precisa, recomiendo:
1. Revisar las directivas más recientes
2. Consultar con el área administrativa competente
3. Verificar actualizaciones normativas

Esta respuesta se genera mediante análisis contextual del sistema RAG MINEDU."""
                
                state["confidence"] = 0.6
            
            # Añadir contexto episódico si es relevante
            if state["episodic_context"].get("relevant_context"):
                response += f"\n\n**Nota:** Esta respuesta considera {len(state['episodic_context']['episodes'])} interacciones previas relacionadas."
            
            state["final_response"] = response
            state["reasoning_chain"].append("Respuesta sintetizada exitosamente")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error sintetizando respuesta: {e}")
            state["final_response"] = "Error generando respuesta. Consulte documentación oficial."
            state["confidence"] = 0.0
            return state
    
    async def _episodic_recorder_node(self, state: RAGState) -> RAGState:
        """Nodo: Registrar episodio en memoria"""
        try:
            session_id = state["metadata"]["session_id"]
            
            # Crear episodio
            episode = {
                "query": state["query"],
                "query_type": state["query_type"],
                "agent_used": state["agent_route"],
                "response": state["final_response"],
                "confidence": state["confidence"],
                "reasoning_chain": state["reasoning_chain"],
                "calculation_result": state["calculation_result"],
                "rag_result": state["rag_result"],
                "timestamp": datetime.now().isoformat()
            }
            
            # Guardar episodio
            await self.episodic_memory.store_episode(
                session_id=session_id,
                episode=episode
            )
            
            state["reasoning_chain"].append("Episodio registrado en memoria")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error registrando episodio: {e}")
            return state
    
    def _determine_next_step(self, state: RAGState) -> str:
        """Determinar siguiente paso después de clasificación"""
        # Si hay contexto episódico relevante disponible, recuperarlo
        if state["metadata"].get("session_id") != "default":
            return "retrieve_episodic"
        else:
            return "route_to_agent"
    
    def _route_agent_decision(self, state: RAGState) -> str:
        """Decidir routing de agente basado en clasificación"""
        agent_route = state["agent_route"]
        
        if "calculation" in agent_route:
            return "calculation"
        elif "rag" in agent_route or "semantic" in agent_route:
            return "semantic_rag"
        else:
            return "context_enhance"
    
    async def _process_query_fallback(self, 
                                    query: str, 
                                    context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Procesamiento fallback sin LangGraph"""
        try:
            # Clasificar query
            classification = self.query_classifier.classify_query(query)
            
            # Ejecutar agente apropiado
            if classification.target_agent == "calculation_agent":
                calc_result = self.calculation_agent.process_calculation_query(query, context)
                return {
                    "answer": f"Cálculo: {calc_result.result_formatted}. {calc_result.legal_basis}",
                    "confidence": calc_result.confidence,
                    "method": "fallback_calculation",
                    "calculation_result": calc_result.__dict__
                }
            else:
                rag_result = self.semantic_rag.search_and_generate(query)
                return {
                    "answer": rag_result["answer"],
                    "confidence": rag_result["confidence"],
                    "method": "fallback_rag",
                    "sources": rag_result.get("sources", [])
                }
                
        except Exception as e:
            logger.error(f"❌ Error en fallback: {e}")
            return {
                "answer": "Error procesando consulta",
                "confidence": 0.0,
                "method": "error"
            }
    
    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del orquestador"""
        return {
            "langgraph_available": LANGGRAPH_AVAILABLE,
            "graph_compiled": self.compiled_graph is not None,
            "agents_loaded": {
                "query_classifier": True,
                "calculation_agent": True,
                "semantic_rag": True,
                "episodic_memory": True
            },
            "graph_nodes": [
                "classify_query", "retrieve_episodic", "route_to_agent",
                "calculation_agent", "semantic_rag_agent", "context_enhancer",
                "response_synthesizer", "episodic_recorder"
            ] if LANGGRAPH_AVAILABLE else [],
            "features": [
                "Multi-agent orchestration",
                "Episodic memory integration", 
                "Contextual enhancement",
                "Reasoning chain tracking",
                "Session persistence"
            ]
        }

# Instancia global
global_langgraph_orchestrator = LangGraphOrchestrator()