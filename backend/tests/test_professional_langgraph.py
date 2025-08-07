"""
Tests profesionales para LangGraph con pytest
Cubre validación, retry, fallback y observabilidad
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from backend.src.langchain_integration.orchestration.professional_langgraph import (
    ProfessionalLangGraphOrchestrator, 
    ProfessionalRAGState
)

class TestProfessionalLangGraph:
    """Suite de tests para LangGraph profesional"""
    
    @pytest.fixture
    def orchestrator(self):
        """Fixture del orquestador profesional"""
        return ProfessionalLangGraphOrchestrator()
    
    @pytest.fixture
    def sample_state(self):
        """Estado de muestra para tests"""
        return {
            "messages": [],
            "query": "¿Cuál es el monto máximo de viáticos en provincias?",
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
    
    # === TESTS DE VALIDACIÓN DE ENTRADA ===
    
    @pytest.mark.asyncio
    async def test_input_validation_valid_query(self, orchestrator, sample_state):
        """Test validación exitosa de entrada"""
        sample_state["query"] = "¿Cuál es el monto máximo de viáticos?"
        
        result = await orchestrator._input_validation_node(sample_state)
        
        assert result["validation_errors"] == []
        assert result["trace_id"].startswith("trace_")
        assert "input_validation" in result["node_history"]
        assert result["max_attempts"] == 3
    
    @pytest.mark.asyncio
    async def test_input_validation_empty_query(self, orchestrator, sample_state):
        """Test validación con query vacía"""
        sample_state["query"] = ""
        
        result = await orchestrator._input_validation_node(sample_state)
        
        assert "Query demasiado corta" in result["validation_errors"]
        assert len(result["error_log"]) > 0
    
    @pytest.mark.asyncio
    async def test_input_validation_malicious_query(self, orchestrator, sample_state):
        """Test validación con contenido malicioso"""
        sample_state["query"] = "<script>alert('hack')</script>"
        
        result = await orchestrator._input_validation_node(sample_state)
        
        assert any("malicioso" in error for error in result["validation_errors"])
    
    @pytest.mark.asyncio
    async def test_input_validation_too_long(self, orchestrator, sample_state):
        """Test validación con query muy larga"""
        sample_state["query"] = "a" * 600  # Más de 500 caracteres
        
        result = await orchestrator._input_validation_node(sample_state)
        
        assert "Query demasiado larga" in result["validation_errors"]
    
    # === TESTS DE DETECCIÓN DE INTENCIÓN ===
    
    @pytest.mark.asyncio
    async def test_detect_intent_viaticos(self, orchestrator, sample_state):
        """Test detección de intención para viáticos"""
        sample_state["query"] = "¿Cuál es el monto máximo de viáticos en provincias?"
        sample_state["node_history"] = []
        
        result = await orchestrator._detect_intent_node(sample_state)
        
        assert result["intent"] == "viaticos"
        assert result["intent_confidence"] > 0.5
        assert "detect_intent" in result["node_history"]
        assert "location" in result["intent_entities"]
    
    @pytest.mark.asyncio
    async def test_detect_intent_declaracion_jurada(self, orchestrator, sample_state):
        """Test detección de intención para declaración jurada"""
        sample_state["query"] = "¿Cuál es el límite para declaración jurada?"
        sample_state["node_history"] = []
        
        result = await orchestrator._detect_intent_node(sample_state)
        
        assert result["intent"] == "declaracion_jurada"
        assert result["intent_confidence"] > 0.3
        assert "detect_intent" in result["node_history"]
    
    @pytest.mark.asyncio
    async def test_detect_intent_general(self, orchestrator, sample_state):
        """Test detección de intención general"""
        sample_state["query"] = "¿Cómo está el clima hoy?"
        sample_state["node_history"] = []
        
        result = await orchestrator._detect_intent_node(sample_state)
        
        assert result["intent"] == "general"
        assert result["intent_confidence"] < 0.5
    
    # === TESTS DE ROUTING ===
    
    @pytest.mark.asyncio
    async def test_route_to_agent_high_confidence(self, orchestrator, sample_state):
        """Test routing con alta confianza"""
        sample_state["intent"] = "viaticos"
        sample_state["intent_confidence"] = 0.8
        sample_state["node_history"] = []
        
        result = await orchestrator._route_to_agent_node(sample_state)
        
        assert result["selected_agent"] == "viaticos"
        assert "route_to_agent" in result["node_history"]
    
    @pytest.mark.asyncio
    async def test_route_to_agent_low_confidence(self, orchestrator, sample_state):
        """Test routing con baja confianza (fallback)"""
        sample_state["intent"] = "unknown"
        sample_state["intent_confidence"] = 0.1
        sample_state["node_history"] = []
        
        result = await orchestrator._route_to_agent_node(sample_state)
        
        assert result["selected_agent"] == "viaticos"  # Agente por defecto
    
    # === TESTS DE EJECUCIÓN DE AGENTE ===
    
    @pytest.mark.asyncio
    async def test_execute_agent_success(self, orchestrator, sample_state):
        """Test ejecución exitosa de agente"""
        sample_state["selected_agent"] = "viaticos"
        sample_state["agent_attempts"] = 0
        sample_state["node_history"] = []
        
        # Mock del agente
        mock_result = {
            "response": "El monto máximo es S/ 320.00 soles",
            "sources": [{"titulo": "Directiva 011", "source": "MINEDU"}],
            "documents_found": 3,
            "confidence": 0.9
        }
        
        with patch.object(orchestrator.agents["viaticos"], 'process_query', 
                         new_callable=AsyncMock, return_value=mock_result):
            
            result = await orchestrator._execute_agent_node(sample_state)
            
            assert result["raw_response"] == "El monto máximo es S/ 320.00 soles"
            assert result["documents_found"] == 3
            assert result["confidence"] == 0.9
            assert len(result["sources"]) == 1
            assert result["agent_attempts"] == 1
    
    @pytest.mark.asyncio
    async def test_execute_agent_error(self, orchestrator, sample_state):
        """Test manejo de error en agente"""
        sample_state["selected_agent"] = "viaticos"
        sample_state["agent_attempts"] = 0
        sample_state["node_history"] = []
        
        # Mock que genera error
        with patch.object(orchestrator.agents["viaticos"], 'process_query', 
                         new_callable=AsyncMock, side_effect=Exception("Agent error")):
            
            result = await orchestrator._execute_agent_node(sample_state)
            
            assert result["raw_response"] == ""
            assert "Error en execute_agent" in str(result["error_log"])
    
    # === TESTS DE VALIDACIÓN DE RESPUESTA ===
    
    @pytest.mark.asyncio
    async def test_validate_response_success(self, orchestrator, sample_state):
        """Test validación exitosa de respuesta"""
        sample_state["raw_response"] = "El monto máximo para viáticos es S/ 320.00 según Directiva 011"
        sample_state["intent"] = "viaticos"
        sample_state["documents_found"] = 3
        sample_state["confidence"] = 0.9
        sample_state["node_history"] = []
        
        result = await orchestrator._validate_response_node(sample_state)
        
        assert result["validated_response"] == True
        assert len(result["evidence_found"]) > 0
        assert len(result["validation_errors"]) == 0
        assert "S/ 320.00" in result["evidence_found"][0] or "320" in str(result["evidence_found"])
    
    @pytest.mark.asyncio
    async def test_validate_response_empty(self, orchestrator, sample_state):
        """Test validación con respuesta vacía"""
        sample_state["raw_response"] = ""
        sample_state["intent"] = "viaticos"
        sample_state["node_history"] = []
        
        result = await orchestrator._validate_response_node(sample_state)
        
        assert result["validated_response"] == False
        assert "Respuesta vacía" in str(result["validation_errors"])
    
    @pytest.mark.asyncio
    async def test_validate_response_no_evidence(self, orchestrator, sample_state):
        """Test validación sin evidencia específica"""
        sample_state["raw_response"] = "No tengo información sobre eso"
        sample_state["intent"] = "viaticos"
        sample_state["documents_found"] = 0
        sample_state["confidence"] = 0.2
        sample_state["node_history"] = []
        
        result = await orchestrator._validate_response_node(sample_state)
        
        assert result["validated_response"] == False
        assert len(result["validation_errors"]) > 0
    
    # === TESTS DE FALLBACK ===
    
    @pytest.mark.asyncio
    async def test_fallback_legacy_viaticos_monto(self, orchestrator, sample_state):
        """Test fallback para consulta de monto de viáticos"""
        sample_state["query"] = "¿cuánto es el monto de viáticos?"
        sample_state["intent"] = "viaticos"
        sample_state["node_history"] = []
        
        result = await orchestrator._fallback_legacy_node(sample_state)
        
        assert result["used_fallback"] == True
        assert "S/ 320.00" in result["raw_response"]
        assert "VIÁTICOS - INFORMACIÓN GENERAL" in result["raw_response"]
        assert len(result["messages"]) > 0
    
    @pytest.mark.asyncio
    async def test_fallback_legacy_general(self, orchestrator, sample_state):
        """Test fallback general"""
        sample_state["query"] = "¿qué es esto?"
        sample_state["intent"] = "general"
        sample_state["node_history"] = []
        
        result = await orchestrator._fallback_legacy_node(sample_state)
        
        assert result["used_fallback"] == True
        assert "No pude encontrar información específica" in result["raw_response"]
    
    # === TESTS DE COMPOSICIÓN ===
    
    @pytest.mark.asyncio
    async def test_compose_response(self, orchestrator, sample_state):
        """Test composición de respuesta final"""
        sample_state["raw_response"] = "El monto es S/ 320.00"
        sample_state["selected_agent"] = "viaticos"
        sample_state["documents_found"] = 3
        sample_state["confidence"] = 0.9
        sample_state["used_fallback"] = False
        sample_state["trace_id"] = "trace_1234567890"
        sample_state["node_history"] = []
        
        result = await orchestrator._compose_response_node(sample_state)
        
        assert "El monto es S/ 320.00" in result["final_response"]
        assert "METADATOS DEL SISTEMA" in result["final_response"]
        assert "Agente: viaticos" in result["final_response"]
        assert "Documentos consultados: 3" in result["final_response"]
        assert result["timestamp"] != ""
    
    # === TESTS DE MANEJO DE ERRORES ===
    
    @pytest.mark.asyncio
    async def test_error_handler(self, orchestrator, sample_state):
        """Test manejo de errores"""
        sample_state["error_log"] = ["Error crítico", "Fallo en agente"]
        sample_state["trace_id"] = "trace_1234567890"
        sample_state["node_history"] = []
        
        result = await orchestrator._error_handler_node(sample_state)
        
        assert "ERROR EN EL SISTEMA" in result["final_response"]
        assert "Error crítico" in result["final_response"]
        assert "Fallo en agente" in result["final_response"]
        assert "trace_1234567890" in result["final_response"]
    
    # === TESTS DE FUNCIONES DE DECISIÓN ===
    
    def test_decide_after_agent_success(self, orchestrator, sample_state):
        """Test decisión después de agente exitoso"""
        sample_state["raw_response"] = "Respuesta válida"
        sample_state["agent_attempts"] = 1
        sample_state["error_log"] = []
        
        decision = orchestrator._decide_after_agent(sample_state)
        
        assert decision == "validate"
    
    def test_decide_after_agent_retry(self, orchestrator, sample_state):
        """Test decisión para retry después de fallo"""
        sample_state["raw_response"] = ""
        sample_state["agent_attempts"] = 1
        sample_state["max_attempts"] = 3
        sample_state["error_log"] = []
        
        decision = orchestrator._decide_after_agent(sample_state)
        
        assert decision == "retry"
    
    def test_decide_after_agent_error(self, orchestrator, sample_state):
        """Test decisión para error después de max intentos"""
        sample_state["raw_response"] = ""
        sample_state["agent_attempts"] = 3
        sample_state["max_attempts"] = 3
        sample_state["error_log"] = []
        
        decision = orchestrator._decide_after_agent(sample_state)
        
        assert decision == "error"
    
    def test_decide_after_validation_success(self, orchestrator, sample_state):
        """Test decisión después de validación exitosa"""
        sample_state["validated_response"] = True
        sample_state["validation_errors"] = []
        
        decision = orchestrator._decide_after_validation(sample_state)
        
        assert decision == "success"
    
    def test_decide_after_validation_fallback(self, orchestrator, sample_state):
        """Test decisión para fallback después de validación fallida"""
        sample_state["validated_response"] = False
        sample_state["validation_errors"] = ["No se encontró evidencia específica"]
        sample_state["agent_attempts"] = 1
        sample_state["max_attempts"] = 3
        
        decision = orchestrator._decide_after_validation(sample_state)
        
        assert decision == "fallback"
    
    # === TESTS DE INTEGRACIÓN ===
    
    @pytest.mark.asyncio
    async def test_full_workflow_integration(self, orchestrator):
        """Test de integración completa del workflow"""
        query = "¿Cuál es el monto máximo de viáticos?"
        
        # Mock del agente para integración
        mock_result = {
            "response": "El monto máximo para viáticos es S/ 320.00 según la Directiva 011-2020-MINEDU",
            "sources": [{"titulo": "Directiva 011", "source": "MINEDU"}],
            "documents_found": 3,
            "confidence": 0.9
        }
        
        with patch.object(orchestrator.agents["viaticos"], 'process_query', 
                         new_callable=AsyncMock, return_value=mock_result):
            
            result = await orchestrator.process_query_professional(query)
            
            assert result["method"] == "professional_langgraph"
            assert "S/ 320.00" in result["response"]
            assert result["confidence"] > 0.8
            assert result["documents_found"] == 3
            assert result["orchestrator_info"]["langgraph_professional"] == True
            assert result["orchestrator_info"]["validation_enabled"] == True
            assert result["orchestrator_info"]["retry_enabled"] == True
    
    @pytest.mark.asyncio
    async def test_full_workflow_with_fallback(self, orchestrator):
        """Test de integración con activación de fallback"""
        query = "¿Qué es algo raro?"
        
        # Mock que genera respuesta vacía para activar fallback
        mock_result = {
            "response": "",
            "sources": [],
            "documents_found": 0,
            "confidence": 0.1
        }
        
        with patch.object(orchestrator.agents["viaticos"], 'process_query', 
                         new_callable=AsyncMock, return_value=mock_result):
            
            result = await orchestrator.process_query_professional(query)
            
            assert result["method"] == "professional_langgraph"
            assert result["extracted_info"]["used_fallback"] == True
            assert "No pude encontrar información específica" in result["response"]
    
    # === TESTS DE CONFIGURACIÓN Y ESTADO ===
    
    def test_system_status(self, orchestrator):
        """Test del estado del sistema"""
        with patch('backend.src.langchain_integration.orchestration.professional_langgraph.retriever') as mock_retriever:
            mock_retriever.get_stats.return_value = {"total_documents": 12}
            
            status = orchestrator.get_system_status()
            
            assert status["orchestrator"] == "professional_langgraph"
            assert status["status"] == "professional_operational"
            assert status["langgraph_version"] == "professional"
            assert status["features"]["input_validation"] == True
            assert status["features"]["automatic_retry"] == True
            assert status["features"]["fallback_system"] == True
            assert status["max_retry_attempts"] == 3
            assert "viaticos" in status["agents"]

# === TESTS DE PERFORMANCE ===

class TestProfessionalLangGraphPerformance:
    """Tests de rendimiento para LangGraph profesional"""
    
    @pytest.mark.asyncio
    async def test_processing_time_benchmark(self):
        """Test benchmark de tiempo de procesamiento"""
        orchestrator = ProfessionalLangGraphOrchestrator()
        query = "¿Cuál es el monto máximo de viáticos?"
        
        # Mock rápido
        mock_result = {
            "response": "S/ 320.00",
            "sources": [],
            "documents_found": 1,
            "confidence": 0.9
        }
        
        with patch.object(orchestrator.agents["viaticos"], 'process_query', 
                         new_callable=AsyncMock, return_value=mock_result):
            
            start_time = asyncio.get_event_loop().time()
            result = await orchestrator.process_query_professional(query)
            end_time = asyncio.get_event_loop().time()
            
            processing_time = end_time - start_time
            
            # El procesamiento debe ser menor a 5 segundos
            assert processing_time < 5.0
            assert result["processing_time"] > 0
    
    @pytest.mark.asyncio
    async def test_retry_performance(self):
        """Test rendimiento con múltiples intentos"""
        orchestrator = ProfessionalLangGraphOrchestrator()
        query = "test retry"
        
        # Mock que falla 2 veces y luego funciona
        call_count = 0
        def mock_agent_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Simulated failure")
            return {
                "response": "Success after retry",
                "sources": [],
                "documents_found": 1,
                "confidence": 0.8
            }
        
        with patch.object(orchestrator.agents["viaticos"], 'process_query', 
                         new_callable=AsyncMock, side_effect=mock_agent_call):
            
            result = await orchestrator.process_query_professional(query)
            
            # Debe haber usado fallback después de 3 intentos fallidos
            assert result["extracted_info"]["agent_attempts"] == 3
            assert result["extracted_info"]["used_fallback"] == True

# === CONFIGURACIÓN DE PYTEST ===

@pytest.fixture(scope="session")
def event_loop():
    """Fixture para event loop de asyncio"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Marcar todos los tests como asyncio
pytest_plugins = ('pytest_asyncio',)