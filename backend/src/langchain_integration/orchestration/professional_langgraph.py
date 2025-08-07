"""
LangGraph PROFESIONAL con arquitectura robusta, trazable y escalable
Combina tu implementación actual con mejores prácticas de ChatGPT
"""
import logging
import time
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from datetime import datetime
import operator
import re

# LangGraph REAL imports
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferMemory

from ..agents.viaticos_agent import viaticos_agent
from ..config import config

logger = logging.getLogger(__name__)

# === ESTADO PROFESIONAL LANGGRAPH ===
class ProfessionalRAGState(TypedDict):
    """Estado completo para RAG profesional con validación y fallback"""
    # Mensajes y conversación
    messages: Annotated[List, add_messages]
    query: str
    conversation_memory: Dict[str, Any]
    
    # Análisis de intención
    intent: str
    intent_confidence: float
    intent_entities: Dict[str, Any]
    
    # Routing y agentes
    selected_agent: str
    agent_attempts: int
    max_attempts: int
    
    # Procesamiento y validación
    raw_response: str
    validated_response: bool
    validation_errors: List[str]
    evidence_found: List[str]
    
    # Fuentes y metadatos
    sources: List[Dict[str, Any]]
    documents_found: int
    confidence: float
    
    # Fallback y composición
    used_fallback: bool
    fallback_reason: str
    final_response: str
    
    # Observabilidad
    processing_time: float
    timestamp: str
    trace_id: str
    node_history: List[str]
    error_log: List[str]

class ProfessionalLangGraphOrchestrator:
    """Orquestador LangGraph PROFESIONAL con validación, retry y observabilidad"""
    
    def __init__(self):
        self.orchestrator_name = "professional_langgraph"
        
        # Agentes especializados
        self.agents = {
            "viaticos": viaticos_agent,
            # Escalable a: "detracciones", "siaf", "snip", etc.
        }
        
        # Patrones de validación para respuestas
        self.validation_patterns = {
            "viaticos": [
                r"S/\s*\d+\.?\d*",  # Montos en soles
                r"\d+\.?\d*\s*soles",  # Soles escritos
                r"artículo\s*\d+",  # Referencias normativas
                r"directiva\s*\d+",  # Directivas
            ],
            "declaracion_jurada": [
                r"declaración\s*jurada",
                r"sin\s*comprobante",
                r"límite|limite",
            ]
        }
        
        # Memoria de conversación
        self.conversation_memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            max_token_limit=2000
        )
        
        # Construir StateGraph profesional
        self.workflow = self._build_professional_stategraph()
        
        # Memory saver para checkpointing
        self.memory = MemorySaver()
        
        # Compilar graph
        self.compiled_graph = self.workflow.compile(checkpointer=self.memory)
        
        logger.info("🚀 LangGraph PROFESIONAL inicializado con validación y retry")
    
    def _build_professional_stategraph(self) -> StateGraph:
        """Construir StateGraph profesional con nodos de validación y fallback"""
        
        workflow = StateGraph(ProfessionalRAGState)
        
        # === NODOS PROFESIONALES ===
        workflow.add_node("input_validation", self._input_validation_node)
        workflow.add_node("detect_intent", self._detect_intent_node)
        workflow.add_node("route_to_agent", self._route_to_agent_node)
        workflow.add_node("execute_agent", self._execute_agent_node)
        workflow.add_node("validate_response", self._validate_response_node)
        workflow.add_node("fallback_legacy", self._fallback_legacy_node)
        workflow.add_node("compose_response", self._compose_response_node)
        workflow.add_node("error_handler", self._error_handler_node)
        
        # === FLUJO PRINCIPAL ===
        workflow.add_edge(START, "input_validation")
        workflow.add_edge("input_validation", "detect_intent")
        workflow.add_edge("detect_intent", "route_to_agent")
        workflow.add_edge("route_to_agent", "execute_agent")
        
        # === CONDITIONAL EDGES CON VALIDACIÓN ===
        workflow.add_conditional_edges(
            "execute_agent",
            self._decide_after_agent,
            {
                "validate": "validate_response",
                "retry": "execute_agent",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "validate_response",
            self._decide_after_validation,
            {
                "success": "compose_response",
                "fallback": "fallback_legacy",
                "retry": "execute_agent"
            }
        )
        
        workflow.add_edge("fallback_legacy", "compose_response")
        workflow.add_edge("compose_response", END)
        workflow.add_edge("error_handler", END)
        
        return workflow
    
    # === NODOS PROFESIONALES ===
    
    async def _input_validation_node(self, state: ProfessionalRAGState) -> ProfessionalRAGState:
        """Validación robusta de entrada"""
        start_time = time.time()
        node_name = "input_validation"
        
        try:
            query = state["query"].strip()
            
            # Validaciones de seguridad
            validation_errors = []
            
            # 1. Longitud mínima/máxima
            if len(query) < 3:
                validation_errors.append("Query demasiado corta")
            elif len(query) > 500:
                validation_errors.append("Query demasiado larga")
            
            # 2. Caracteres maliciosos básicos
            malicious_patterns = [
                r"<script",
                r"javascript:",
                r"eval\(",
                r"exec\(",
                r"__import__"
            ]
            
            for pattern in malicious_patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    validation_errors.append(f"Patrón malicioso detectado: {pattern}")
            
            # 3. Solo espacios o caracteres especiales
            if not re.search(r"[a-zA-ZáéíóúÁÉÍÓÚñÑ]", query):
                validation_errors.append("Query sin contenido textual válido")
            
            # Actualizar estado
            state["validation_errors"] = validation_errors
            state["trace_id"] = f"trace_{int(time.time())}"
            state["node_history"] = [node_name]
            state["max_attempts"] = 3
            state["agent_attempts"] = 0
            
            if validation_errors:
                state["error_log"] = validation_errors
                logger.warning(f"❌ [{node_name}] Errores de validación: {validation_errors}")
            else:
                logger.info(f"✅ [{node_name}] Input válido: '{query[:50]}...'")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ [{node_name}] Error: {e}")
            state["error_log"] = [f"Error en {node_name}: {str(e)}"]
            return state
    
    async def _detect_intent_node(self, state: ProfessionalRAGState) -> ProfessionalRAGState:
        """Detección avanzada de intención con entidades"""
        node_name = "detect_intent"
        state["node_history"].append(node_name)
        
        try:
            query = state["query"].lower()
            
            # Patrones mejorados de intención
            intent_patterns = {
                "viaticos": {
                    "patterns": ["viático", "viaticos", "viáticos", "monto", "gastos", "comisión"],
                    "entities": {
                        "amount": r"(s/\s*\d+\.?\d*|\d+\.?\d*\s*soles)",
                        "location": r"(lima|provincia|provincias|metropolitana|regional)",
                        "type": r"(declaración jurada|sin comprobante|con comprobante)"
                    }
                },
                "declaracion_jurada": {
                    "patterns": ["declaración jurada", "declaracion jurada", "sin comprobante"],
                    "entities": {
                        "limit": r"(límite|limite|máximo|maximo|tope)",
                        "location": r"(lima|provincia|provincias)"
                    }
                }
            }
            
            # Calcular scores de intención
            intent_scores = {}
            entities_found = {}
            
            for intent, config in intent_patterns.items():
                score = 0
                entities = {}
                
                # Score por patrones
                for pattern in config["patterns"]:
                    if pattern in query:
                        score += len(pattern) * 2  # Peso por longitud
                
                # Extraer entidades
                for entity_type, entity_pattern in config["entities"].items():
                    matches = re.findall(entity_pattern, query, re.IGNORECASE)
                    if matches:
                        entities[entity_type] = matches
                        score += len(matches) * 3  # Bonus por entidades
                
                if score > 0:
                    intent_scores[intent] = score
                    entities_found[intent] = entities
            
            # Determinar intención principal
            if intent_scores:
                primary_intent = max(intent_scores.keys(), key=lambda x: intent_scores[x])
                confidence = min(intent_scores[primary_intent] / 15, 1.0)
                intent_entities = entities_found.get(primary_intent, {})
            else:
                primary_intent = "general"
                confidence = 0.2
                intent_entities = {}
            
            # Actualizar estado
            state["intent"] = primary_intent
            state["intent_confidence"] = confidence
            state["intent_entities"] = intent_entities
            
            logger.info(f"🧠 [{node_name}] Intent: {primary_intent} (conf: {confidence:.2f})")
            logger.info(f"🎯 [{node_name}] Entidades: {intent_entities}")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ [{node_name}] Error: {e}")
            state["error_log"].append(f"Error en {node_name}: {str(e)}")
            return state
    
    async def _route_to_agent_node(self, state: ProfessionalRAGState) -> ProfessionalRAGState:
        """Routing inteligente a agentes especializados"""
        node_name = "route_to_agent"
        state["node_history"].append(node_name)
        
        try:
            intent = state["intent"]
            confidence = state["intent_confidence"]
            
            # Lógica de routing mejorada
            if confidence > 0.6 and intent in self.agents:
                selected_agent = intent
            elif confidence > 0.3 and intent in self.agents:
                selected_agent = intent  # Intentar con confianza media
            else:
                selected_agent = "viaticos"  # Agente por defecto
            
            state["selected_agent"] = selected_agent
            
            logger.info(f"🚦 [{node_name}] Routing: {state['query'][:30]}... → {selected_agent}")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ [{node_name}] Error: {e}")
            state["error_log"].append(f"Error en {node_name}: {str(e)}")
            return state
    
    async def _execute_agent_node(self, state: ProfessionalRAGState) -> ProfessionalRAGState:
        """Ejecución de agente con retry automático"""
        node_name = "execute_agent"
        state["node_history"].append(node_name)
        
        try:
            selected_agent = state["selected_agent"]
            state["agent_attempts"] += 1
            
            logger.info(f"🤖 [{node_name}] Ejecutando {selected_agent} (intento {state['agent_attempts']})")
            
            # Ejecutar agente real
            agent = self.agents[selected_agent]
            agent_result = await agent.process_query(state["query"])
            
            # Extraer información del resultado
            raw_response = agent_result.get("response", "")
            sources = agent_result.get("sources", [])
            documents_found = agent_result.get("documents_found", 0)
            confidence = agent_result.get("confidence", 0.0)
            
            # 🚀 ENTERPRISE ENHANCEMENT: Advanced Reranking
            try:
                if sources and len(sources) > 1:
                    logger.info(f"🔄 [{node_name}] Aplicando reranking avanzado a {len(sources)} documentos")
                    
                    # Importar reranker (usando path relativo correcto)
                    try:
                        from ...core.reranking.advanced_reranker import rerank_search_results
                    except ImportError:
                        # Fallback import
                        import sys
                        from pathlib import Path
                        backend_dir = Path(__file__).parent.parent.parent.parent
                        sys.path.insert(0, str(backend_dir / "src"))
                        from core.reranking.advanced_reranker import rerank_search_results
                    
                    # Preparar documentos para reranking
                    documents_for_rerank = []
                    for i, source in enumerate(sources):
                        doc = {
                            "id": str(i),
                            "content": source.get("content", ""),
                            "text": source.get("content", ""),  # Fallback
                            "score": source.get("score", 0.5),
                            "source": source.get("source", ""),
                            "title": source.get("title", "")
                        }
                        documents_for_rerank.append(doc)
                    
                    # Aplicar reranking híbrido
                    reranked_results = await rerank_search_results(
                        query=state["query"],
                        documents=documents_for_rerank,
                        strategy="hybrid"  # hybrid, cross_encoder, semantic, fallback
                    )
                    
                    if reranked_results:
                        # Actualizar sources con resultados reranqueados
                        reranked_sources = []
                        for result in reranked_results:
                            reranked_source = {
                                "content": result.content,
                                "source": result.metadata.get("source", ""),
                                "title": result.metadata.get("title", ""),
                                "score": result.reranked_score,
                                "original_score": result.original_score,
                                "confidence": result.confidence,
                                "ranking_method": result.ranking_method,
                                "original_rank": result.metadata.get("original_rank", 0)
                            }
                            reranked_sources.append(reranked_source)
                        
                        sources = reranked_sources
                        
                        # Actualizar confianza basada en reranking
                        if reranked_results:
                            top_confidence = reranked_results[0].confidence
                            confidence = max(confidence, top_confidence)  # Tomar la mejor confianza
                        
                        logger.info(f"✅ [{node_name}] Reranking completado: top score {reranked_results[0].reranked_score:.3f}, método: {reranked_results[0].ranking_method}")
                    else:
                        logger.warning(f"⚠️ [{node_name}] Reranking no produjo resultados, usando originales")
                        
                else:
                    logger.info(f"ℹ️ [{node_name}] Reranking omitido: {len(sources)} documentos disponibles")
                    
            except Exception as rerank_error:
                logger.warning(f"⚠️ [{node_name}] Error en reranking: {rerank_error}, continuando con documentos originales")
                # Continuar con documentos originales si el reranking falla
            
            # Actualizar estado
            state["raw_response"] = raw_response
            state["sources"] = sources
            state["documents_found"] = documents_found
            state["confidence"] = confidence
            
            # Agregar mensaje AI
            ai_message = AIMessage(content=raw_response)
            state["messages"].append(ai_message)
            
            logger.info(f"✅ [{node_name}] Agente completado: {len(raw_response)} chars, {documents_found} docs")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ [{node_name}] Error: {e}")
            state["error_log"].append(f"Error en {node_name}: {str(e)}")
            state["raw_response"] = ""
            return state
    
    async def _validate_response_node(self, state: ProfessionalRAGState) -> ProfessionalRAGState:
        """Validación robusta de respuesta con evidencia"""
        node_name = "validate_response"
        state["node_history"].append(node_name)
        
        try:
            raw_response = state["raw_response"]
            intent = state["intent"]
            
            validation_errors = []
            evidence_found = []
            
            # 1. Validación básica
            if not raw_response or len(raw_response.strip()) < 10:
                validation_errors.append("Respuesta vacía o muy corta")
            
            # 2. Validación específica por intención
            if intent in self.validation_patterns:
                patterns = self.validation_patterns[intent]
                pattern_matches = 0
                
                for pattern in patterns:
                    matches = re.findall(pattern, raw_response, re.IGNORECASE)
                    if matches:
                        pattern_matches += 1
                        evidence_found.extend(matches)
                
                if pattern_matches == 0:
                    validation_errors.append(f"No se encontró evidencia específica para {intent}")
            
            # 3. Validación de fuentes
            if state["documents_found"] == 0:
                validation_errors.append("No se encontraron documentos de respaldo")
            elif state["confidence"] < 0.5:
                validation_errors.append("Confianza muy baja en la respuesta")
            
            # 4. Validación de contenido malicioso en respuesta
            malicious_in_response = [
                r"error|exception|traceback",
                r"none|null|undefined",
                r"<script|javascript:"
            ]
            
            for pattern in malicious_in_response:
                if re.search(pattern, raw_response, re.IGNORECASE):
                    validation_errors.append(f"Contenido problemático en respuesta")
            
            # Actualizar estado
            state["validation_errors"] = validation_errors
            state["evidence_found"] = evidence_found
            state["validated_response"] = len(validation_errors) == 0
            
            if validation_errors:
                logger.critical(f"⚠️ [{node_name}] ERRORES CRÍTICOS DE VALIDACIÓN: {validation_errors}")
                # TODO: Implementar sistema de respuesta segura para errores de validación
            else:
                logger.info(f"✅ [{node_name}] Respuesta válida con evidencia: {evidence_found}")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ [{node_name}] Error: {e}")
            state["error_log"].append(f"Error en {node_name}: {str(e)}")
            state["validated_response"] = False
            return state
    
    async def _fallback_legacy_node(self, state: ProfessionalRAGState) -> ProfessionalRAGState:
        """Sistema de fallback con respuestas de emergencia"""
        node_name = "fallback_legacy"
        state["node_history"].append(node_name)
        
        try:
            logger.critical("⚠️ FALLBACK ACTIVADO - No se encontró información en documentos oficiales")
            # TODO: Reemplazar fallback con consulta real a base de datos normativa
            query = state["query"].lower()
            intent = state["intent"]
            
            # Fallbacks específicos por dominio - SOLO PARA EMERGENCIA
            fallback_responses = {
                "viaticos": {
                    "monto": """📋 **CONSULTA DE VIÁTICOS:**
                    
⚠️ **INFORMACIÓN NO DISPONIBLE:**
• Los montos específicos deben consultarse en la normativa vigente
• Consulte la Directiva N° 011-2020-MINEDU para información exacta

📞 **RECOMENDACIÓN:** Contacte directamente al área administrativa para obtener los montos actualizados.""",
                    
                    "procedimiento": """📋 **PROCEDIMIENTO GENERAL PARA VIÁTICOS:**

📝 **PASOS BÁSICOS:**
1. Solicitud con 5 días de anticipación
2. Aprobación del jefe inmediato
3. Asignación según escala vigente
4. Rendición en 10 días hábiles

⚠️ **NOTA:** Consulte la Directiva N° 011-2020-MINEDU para procedimiento completo."""
                }
            }
            
            # Determinar tipo de fallback
            fallback_type = "general"
            if "monto" in query or "cuanto" in query or "s/" in query:
                fallback_type = "monto"
            elif "procedimiento" in query or "como" in query or "pasos" in query:
                fallback_type = "procedimiento"
            
            # Obtener respuesta de fallback
            if intent in fallback_responses and fallback_type in fallback_responses[intent]:
                fallback_response = fallback_responses[intent][fallback_type]
            else:
                logger.critical("⚠️ Fallback general activado - consulta sin información documental disponible")
                # TODO: Implementar búsqueda avanzada en base de datos normativa
                fallback_response = """📋 **CONSULTA RECIBIDA:**

❌ No se encontró información específica en los documentos oficiales disponibles.

🔍 **ESTADO DEL SISTEMA:**
• Base de datos consultada: Documentos normativos MINEDU
• Resultado: Sin coincidencias verificables

💡 **RECOMENDACIONES:**
• Reformule su consulta con términos oficiales específicos
• Consulte directamente las directivas vigentes del MINEDU
• Contacte al área administrativa correspondiente

⚠️ **IMPORTANTE:** Este sistema solo proporciona información basada en documentos oficiales verificados."""
            
            # Actualizar estado
            state["raw_response"] = fallback_response
            state["used_fallback"] = True
            state["fallback_reason"] = f"Validación falló: {state.get('validation_errors', [])}"
            
            # Agregar mensaje de fallback
            fallback_message = AIMessage(content=fallback_response)
            state["messages"].append(fallback_message)
            
            logger.critical(f"🔄 [{node_name}] FALLBACK CRÍTICO ACTIVADO: {fallback_type} - sistema sin datos documentales")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ [{node_name}] Error: {e}")
            state["error_log"].append(f"Error en {node_name}: {str(e)}")
            return state
    
    async def _compose_response_node(self, state: ProfessionalRAGState) -> ProfessionalRAGState:
        """Composición final de respuesta con metadatos"""
        node_name = "compose_response"
        state["node_history"].append(node_name)
        
        try:
            raw_response = state["raw_response"]
            
            # Agregar metadatos de transparencia
            response_footer = f"""

---
📊 **METADATOS DEL SISTEMA:**
• Agente: {state.get('selected_agent', 'N/A')}
• Documentos consultados: {state.get('documents_found', 0)}
• Confianza: {state.get('confidence', 0):.1%}
• Fallback usado: {'Sí' if state.get('used_fallback') else 'No'}
• Trace ID: {state.get('trace_id', 'N/A')}"""
            
            final_response = raw_response + response_footer
            
            # Actualizar estado final
            state["final_response"] = final_response
            state["timestamp"] = datetime.now().isoformat()
            state["processing_time"] = time.time() - float(state["trace_id"].split("_")[1])
            
            logger.info(f"📝 [{node_name}] Respuesta final compuesta: {len(final_response)} chars")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ [{node_name}] Error: {e}")
            state["error_log"].append(f"Error en {node_name}: {str(e)}")
            state["final_response"] = state.get("raw_response", "Error procesando respuesta")
            return state
    
    async def _error_handler_node(self, state: ProfessionalRAGState) -> ProfessionalRAGState:
        """Manejo robusto de errores"""
        node_name = "error_handler"
        state["node_history"].append(node_name)
        
        try:
            error_log = state.get("error_log", [])
            
            # TODO: Implementar sistema de respuesta de error seguro para producción
            logger.critical(f"⚠️ SISTEMA EN ERROR - múltiples fallos detectados: {len(error_log)} errores")
            
            error_response = f"""❌ **CONSULTA NO DISPONIBLE:**

🔍 **ESTADO DEL SISTEMA:**
• El sistema no puede procesar la consulta en este momento
• Se han consultado las bases de datos oficiales disponibles

🆘 **RECOMENDACIONES:**
• Reformule su consulta con términos más específicos
• Consulte directamente las directivas vigentes del MINEDU
• Contacte al área administrativa correspondiente

📞 **SOPORTE:** Área de Sistemas - Administración MINEDU
⏰ **FECHA:** {datetime.now().strftime('%d/%m/%Y %H:%M')}"""
            
            state["final_response"] = error_response
            state["timestamp"] = datetime.now().isoformat()
            
            logger.critical(f"💥 [{node_name}] Error del sistema manejado - {len(error_log)} errores registrados")
            
            return state
            
        except Exception as e:
            logger.critical(f"❌ [{node_name}] Error crítico en manejo de errores: {e}")
            state["final_response"] = "Error crítico del sistema. Contacte al administrador."
            return state
    
    # === FUNCIONES DE DECISIÓN ===
    
    def _decide_after_agent(self, state: ProfessionalRAGState) -> str:
        """Decidir siguiente paso después de ejecutar agente"""
        try:
            # Si hay errores en el log, manejar error
            if state.get("error_log") and any("Error en execute_agent" in error for error in state["error_log"]):
                if state["agent_attempts"] < state["max_attempts"]:
                    logger.info(f"🔄 Retry agente: intento {state['agent_attempts']}/{state['max_attempts']}")
                    return "retry"
                else:
                    logger.warning(f"💥 Max intentos alcanzados, enviando a error handler")
                    return "error"
            
            # Si la respuesta está vacía, retry o error
            if not state.get("raw_response", "").strip():
                if state["agent_attempts"] < state["max_attempts"]:
                    return "retry"
                else:
                    return "error"
            
            # Continuar con validación
            return "validate"
            
        except Exception as e:
            logger.error(f"Error en decisión post-agente: {e}")
            return "error"
    
    def _decide_after_validation(self, state: ProfessionalRAGState) -> str:
        """Decidir siguiente paso después de validar respuesta"""
        try:
            validated = state.get("validated_response", False)
            validation_errors = state.get("validation_errors", [])
            
            # Si la validación es exitosa
            if validated:
                logger.info("✅ Validación exitosa, componiendo respuesta")
                return "success"
            
            # Si hay errores críticos y ya agotamos intentos
            if state["agent_attempts"] >= state["max_attempts"]:
                logger.warning("⚠️ Max intentos alcanzados, usando fallback")
                return "fallback"
            
            # Si son errores de contenido (no técnicos), usar fallback
            content_errors = ["No se encontró evidencia", "Confianza muy baja", "No se encontraron documentos"]
            has_content_errors = any(any(content_error in error for content_error in content_errors) 
                                   for error in validation_errors)
            
            if has_content_errors:
                logger.info("🔄 Errores de contenido, usando fallback")
                return "fallback"
            
            # Para otros errores, retry
            logger.info("🔄 Errores técnicos, reintentando agente")
            return "retry"
            
        except Exception as e:
            logger.error(f"Error en decisión post-validación: {e}")
            return "fallback"
    
    # === API PRINCIPAL ===
    
    async def process_query_professional(self, query: str, thread_id: str = None) -> Dict[str, Any]:
        """Procesar consulta con LangGraph profesional"""
        start_time = time.time()
        
        if not thread_id:
            thread_id = f"prof_{int(time.time())}"
        
        try:
            logger.info(f"🚀 [PROFESSIONAL] Procesando: {query[:50]}...")
            
            # Estado inicial profesional
            initial_state = {
                "messages": [HumanMessage(content=query)],
                "query": query,
                "conversation_memory": {},
                "intent": "",
                "intent_confidence": 0.0,
                "intent_entities": {},
                "selected_agent": "",
                "agent_attempts": 0,
                "max_attempts": 3,
                "raw_response": "",
                "validated_response": False,
                "validation_errors": [],
                "evidence_found": [],
                "sources": [],
                "documents_found": 0,
                "confidence": 0.0,
                "used_fallback": False,
                "fallback_reason": "",
                "final_response": "",
                "processing_time": 0.0,
                "timestamp": "",
                "trace_id": "",
                "node_history": [],
                "error_log": []
            }
            
            # Configuración de thread
            config_thread = {"configurable": {"thread_id": thread_id}}
            
            # ¡EJECUTAR LANGGRAPH PROFESIONAL!
            final_state = await self.compiled_graph.ainvoke(
                initial_state,
                config=config_thread
            )
            
            # Calcular tiempo total
            total_time = time.time() - start_time
            
            # Resultado profesional
            result = {
                "response": final_state.get("final_response", ""),
                "sources": final_state.get("sources", []),
                "confidence": final_state.get("confidence", 0.0),
                "documents_found": final_state.get("documents_found", 0),
                "intent": final_state.get("intent", ""),
                "intent_entities": final_state.get("intent_entities", {}),
                "extracted_info": {
                    "evidence_found": final_state.get("evidence_found", []),
                    "validation_errors": final_state.get("validation_errors", []),
                    "used_fallback": final_state.get("used_fallback", False),
                    "fallback_reason": final_state.get("fallback_reason", ""),
                    "agent_attempts": final_state.get("agent_attempts", 0)
                },
                "processing_time": round(total_time, 3),
                "method": "professional_langgraph",
                "agent_used": final_state.get("selected_agent", ""),
                "orchestrator_info": {
                    "orchestrator": self.orchestrator_name,
                    "thread_id": thread_id,
                    "trace_id": final_state.get("trace_id", ""),
                    "node_history": final_state.get("node_history", []),
                    "total_processing_time": round(total_time, 3),
                    "timestamp": datetime.now().isoformat(),
                    "langgraph_professional": True,
                    "validation_enabled": True,
                    "retry_enabled": True,
                    "fallback_enabled": True
                }
            }
            
            logger.info(f"✅ [PROFESSIONAL] Completado en {total_time:.3f}s")
            logger.info(f"📊 [PROFESSIONAL] Nodos: {final_state.get('node_history', [])}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ [PROFESSIONAL] Error crítico: {e}")
            return {
                "response": f"Error crítico en LangGraph profesional: {str(e)}",
                "sources": [],
                "confidence": 0.0,
                "error": str(e),
                "method": "professional_langgraph_error",
                "orchestrator_info": {
                    "orchestrator": self.orchestrator_name,
                    "error": True,
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Estado del sistema profesional"""
        try:
            from ..vectorstores.simple_retriever import retriever
            retriever_stats = retriever.get_stats()
            
            return {
                "orchestrator": self.orchestrator_name,
                "status": "professional_operational",
                "langgraph_version": "professional",
                "features": {
                    "input_validation": True,
                    "intent_detection": True,
                    "agent_routing": True,
                    "response_validation": True,
                    "automatic_retry": True,
                    "fallback_system": True,
                    "conversation_memory": True,
                    "observability": True,
                    "error_handling": True
                },
                "agents": {name: {"available": True, "type": type(agent).__name__} 
                          for name, agent in self.agents.items()},
                "validation_patterns": list(self.validation_patterns.keys()),
                "max_retry_attempts": 3,
                "retriever_stats": retriever_stats,
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

# Instancia global profesional
professional_orchestrator = ProfessionalLangGraphOrchestrator()