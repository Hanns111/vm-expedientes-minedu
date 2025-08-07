"""
Streamlit UI profesional para sistema RAG con LangGraph
Incluye autenticación, observabilidad y visualización de flujos
"""
import streamlit as st
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
import base64
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="MINEDU RAG Professional",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuración del backend
BACKEND_URL = "http://localhost:8000"
if "BACKEND_URL" in st.secrets:
    BACKEND_URL = st.secrets["BACKEND_URL"]

# CSS personalizado
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #1f4e79 0%, #2e5984 100%);
    color: white;
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 2rem;
}

.metric-card {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #1f4e79;
}

.trace-info {
    background: #e3f2fd;
    padding: 0.5rem;
    border-radius: 0.25rem;
    font-family: monospace;
    font-size: 0.8rem;
}

.error-box {
    background: #ffebee;
    border: 1px solid #f44336;
    padding: 1rem;
    border-radius: 0.5rem;
    color: #d32f2f;
}

.success-box {
    background: #e8f5e8;
    border: 1px solid #4caf50;
    padding: 1rem;
    border-radius: 0.5rem;
    color: #2e7d32;
}
</style>
""", unsafe_allow_html=True)

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Autenticar usuario y obtener token JWT"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/login",
            json={"username": username, "password": password}
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error de autenticación: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error conectando al backend: {e}")
        return None

def get_system_status(token: str) -> Optional[Dict[str, Any]]:
    """Obtener estado del sistema"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BACKEND_URL}/status", headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

def query_rag_system(query: str, token: str, method: str = "professional") -> Optional[Dict[str, Any]]:
    """Consultar el sistema RAG"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        endpoint = f"/api/chat/{method}"
        
        response = requests.post(
            f"{BACKEND_URL}{endpoint}",
            json={"query": query},
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error en consulta: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error en la consulta: {e}")
        return None

def run_coverage_test(token: str) -> Optional[Dict[str, Any]]:
    """Ejecutar tests de coverage"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BACKEND_URL}/testing/coverage", headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

def evaluate_with_ragas(query: str, response: str, contexts: list, token: str) -> Optional[Dict[str, Any]]:
    """Evaluar respuesta con RAGAS"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "query": query,
            "response": response,
            "contexts": contexts
        }
        response = requests.post(f"{BACKEND_URL}/evaluation/ragas", json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

def main():
    """Aplicación principal"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎓 MINEDU RAG Professional</h1>
        <p>Sistema de consulta de documentos administrativos con LangGraph y JWT</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Estado de sesión
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.token = None
        st.session_state.user_info = None
    
    # Sidebar para autenticación
    with st.sidebar:
        st.header("🔐 Autenticación")
        
        if not st.session_state.authenticated:
            with st.form("login_form"):
                st.write("**Credenciales de acceso:**")
                username = st.text_input("Usuario", value="admin")
                password = st.text_input("Contraseña", type="password", value="admin123")
                
                st.write("**Usuarios disponibles:**")
                st.write("• admin / admin123 (roles: admin, user)")
                st.write("• consultor / consultor123 (role: user)")
                st.write("• demo / demo123 (role: demo)")
                
                if st.form_submit_button("🚀 Iniciar Sesión"):
                    auth_result = authenticate_user(username, password)
                    if auth_result:
                        st.session_state.authenticated = True
                        st.session_state.token = auth_result["access_token"]
                        st.session_state.user_info = auth_result["user"]
                        st.success("✅ Autenticación exitosa")
                        st.rerun()
        else:
            st.success(f"👤 **{st.session_state.user_info['full_name']}**")
            st.write(f"Roles: {', '.join(st.session_state.user_info['roles'])}")
            
            if st.button("🚪 Cerrar Sesión"):
                st.session_state.authenticated = False
                st.session_state.token = None
                st.session_state.user_info = None
                st.rerun()
    
    # Contenido principal (solo si está autenticado)
    if not st.session_state.authenticated:
        st.warning("🔒 Por favor, inicia sesión para acceder al sistema.")
        return
    
    # Tabs principales
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💬 Consultas RAG", 
        "📊 Estado del Sistema", 
        "🧪 Testing", 
        "📈 Evaluación RAGAS", 
        "🔍 Visualización"
    ])
    
    with tab1:
        st.header("💬 Consultas al Sistema RAG")
        
        # Configuración de consulta
        col1, col2 = st.columns([3, 1])
        
        with col1:
            query = st.text_area(
                "Ingresa tu consulta:",
                placeholder="Ejemplo: ¿Cuál es el monto máximo de viáticos en provincias?",
                height=100
            )
        
        with col2:
            method = st.selectbox(
                "Método:",
                ["professional", "real", "hybrid"],
                help="professional: LangGraph con validación, real: LangGraph básico, hybrid: Sistema tradicional"
            )
            
            if st.button("🚀 Consultar", type="primary"):
                if query.strip():
                    with st.spinner("🤖 Procesando consulta..."):
                        start_time = time.time()
                        result = query_rag_system(query.strip(), st.session_state.token, method)
                        end_time = time.time()
                        
                        if result:
                            # Respuesta principal
                            st.markdown("### 📋 Respuesta:")
                            st.markdown(f"""
                            <div class="success-box">
                            {result.get('response', 'Sin respuesta')}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Información del trace
                            if 'extracted_info' in result:
                                info = result['extracted_info']
                                trace_id = info.get('trace_id', 'N/A')
                                
                                st.markdown("### 🔍 Información de Trazabilidad:")
                                st.markdown(f"""
                                <div class="trace-info">
                                <strong>Trace ID:</strong> {trace_id}<br>
                                <strong>Método:</strong> {result.get('method', 'N/A')}<br>
                                <strong>Tiempo:</strong> {end_time - start_time:.2f}s<br>
                                <strong>Agente usado:</strong> {info.get('selected_agent', 'N/A')}<br>
                                <strong>Intentos:</strong> {info.get('agent_attempts', 0)}<br>
                                <strong>Fallback usado:</strong> {'Sí' if info.get('used_fallback') else 'No'}
                                </div>
                                """, unsafe_allow_html=True)
                            
                            # Métricas
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("📄 Documentos", result.get('documents_found', 0))
                            
                            with col2:
                                confidence = result.get('confidence', 0)
                                st.metric("🎯 Confianza", f"{confidence:.1%}")
                            
                            with col3:
                                processing_time = result.get('processing_time', end_time - start_time)
                                st.metric("⏱️ Tiempo", f"{processing_time:.2f}s")
                            
                            with col4:
                                status = "✅ Exitoso" if confidence > 0.7 else "⚠️ Revisar"
                                st.metric("🔍 Estado", status)
                            
                            # Fuentes y evidencia
                            if 'sources' in result and result['sources']:
                                st.markdown("### 📚 Fuentes:")
                                for i, source in enumerate(result['sources'][:3]):
                                    with st.expander(f"Fuente {i+1}: {source.get('titulo', 'Sin título')}"):
                                        st.write(source.get('contenido', 'Sin contenido')[:500] + "...")
                            
                            # Mostrar información técnica completa
                            with st.expander("🔧 Información Técnica Completa"):
                                st.json(result)
                else:
                    st.warning("⚠️ Por favor, ingresa una consulta.")
    
    with tab2:
        st.header("📊 Estado del Sistema")
        
        if st.button("🔄 Actualizar Estado"):
            with st.spinner("Obteniendo estado del sistema..."):
                status = get_system_status(st.session_state.token)
                
                if status:
                    # Estado general
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("""
                        <div class="metric-card">
                        <h4>🚀 Orquestador</h4>
                        <p>{}</p>
                        </div>
                        """.format(status.get('orchestrator', 'N/A')), unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown("""
                        <div class="metric-card">
                        <h4>📊 Estado</h4>
                        <p>{}</p>
                        </div>
                        """.format(status.get('status', 'N/A')), unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown("""
                        <div class="metric-card">
                        <h4>📄 Documentos</h4>
                        <p>{}</p>
                        </div>
                        """.format(status.get('documents_loaded', 0)), unsafe_allow_html=True)
                    
                    # Features disponibles
                    if 'features' in status:
                        st.markdown("### ⚙️ Características Disponibles:")
                        features = status['features']
                        
                        feature_cols = st.columns(2)
                        for i, (feature, enabled) in enumerate(features.items()):
                            with feature_cols[i % 2]:
                                icon = "✅" if enabled else "❌"
                                st.write(f"{icon} **{feature.replace('_', ' ').title()}**")
                    
                    # Información completa
                    with st.expander("📋 Estado Completo del Sistema"):
                        st.json(status)
                else:
                    st.error("❌ No se pudo obtener el estado del sistema")
    
    with tab3:
        st.header("🧪 Testing y Coverage")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("▶️ Ejecutar Tests de Coverage"):
                with st.spinner("Ejecutando tests..."):
                    result = run_coverage_test(st.session_state.token)
                    
                    if result and result.get('passed_threshold'):
                        st.success(f"✅ Tests completados - Coverage: {result.get('coverage_data', {}).get('total_coverage', 0)}%")
                        
                        # Mostrar métricas de coverage
                        coverage_data = result.get('coverage_data', {})
                        
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("📊 Coverage Total", f"{coverage_data.get('total_coverage', 0):.1f}%")
                        with col_b:
                            st.metric("📄 Líneas Cubiertas", coverage_data.get('lines_covered', 0))
                        with col_c:
                            st.metric("📁 Archivos", coverage_data.get('files_analyzed', 0))
                    else:
                        st.error("❌ Tests fallaron o coverage insuficiente")
        
        with col2:
            st.markdown("""
            **Comandos de Testing:**
            ```bash
            # Coverage completo
            make test
            
            # Solo tests rápidos
            make test-fast
            
            # Tests de integración
            make test-integration
            ```
            """)
    
    with tab4:
        st.header("📈 Evaluación RAGAS")
        
        st.write("Evaluar la calidad de las respuestas usando métricas RAGAS")
        
        # Input para evaluación manual
        with st.form("ragas_evaluation"):
            eval_query = st.text_input("Consulta:", value="¿Cuál es el monto máximo de viáticos?")
            eval_response = st.text_area("Respuesta a evaluar:", value="El monto máximo es S/ 320.00 según la Directiva 011-2020")
            eval_contexts = st.text_area("Contextos (uno por línea):", value="El monto máximo para viáticos es S/ 320.00\nEstablecido en la Directiva 011-2020-MINEDU")
            
            if st.form_submit_button("📊 Evaluar con RAGAS"):
                contexts_list = [ctx.strip() for ctx in eval_contexts.split('\n') if ctx.strip()]
                
                with st.spinner("Evaluando con RAGAS..."):
                    evaluation = evaluate_with_ragas(eval_query, eval_response, contexts_list, st.session_state.token)
                    
                    if evaluation:
                        st.success("✅ Evaluación completada")
                        
                        # Mostrar métricas
                        if 'metrics' in evaluation:
                            st.markdown("### 📊 Métricas RAGAS:")
                            
                            metrics_cols = st.columns(len(evaluation['metrics']))
                            for i, (metric_name, metric_data) in enumerate(evaluation['metrics'].items()):
                                with metrics_cols[i]:
                                    score = metric_data.get('score', 0)
                                    interpretation = metric_data.get('interpretation', '')
                                    
                                    st.metric(
                                        metric_name.replace('_', ' ').title(),
                                        f"{score:.3f}",
                                        help=interpretation
                                    )
                        
                        # Score general
                        overall_score = evaluation.get('overall_score', 0)
                        if overall_score >= 0.8:
                            st.success(f"🎉 Score general: {overall_score:.3f} (Excelente)")
                        elif overall_score >= 0.6:
                            st.info(f"👍 Score general: {overall_score:.3f} (Bueno)")
                        else:
                            st.warning(f"⚠️ Score general: {overall_score:.3f} (Necesita mejora)")
                    else:
                        st.error("❌ Error en la evaluación RAGAS")
    
    with tab5:
        st.header("🔍 Visualización del Sistema")
        
        st.markdown("""
        ### 🎯 LangGraph Workflow
        
        El sistema utiliza el siguiente flujo profesional:
        
        ```mermaid
        graph TD
            A[Input Validation] --> B[Detect Intent]
            B --> C[Route to Agent]
            C --> D[Execute Agent]
            D --> E{Success?}
            E -->|Yes| F[Validate Response]
            E -->|No| G{Retry?}
            G -->|Yes| D
            G -->|No| H[Fallback Legacy]
            F --> I{Valid?}
            I -->|Yes| J[Compose Response]
            I -->|No| H
            H --> J
            J --> K[End]
            
            style A fill:#e1f5fe
            style J fill:#e8f5e8
            style H fill:#fff3e0
        ```
        
        ### 🚀 Características Profesionales:
        - ✅ **Validación de entrada** con sanitización
        - ✅ **Detección de intención** con confianza
        - ✅ **Routing inteligente** por tipo de consulta
        - ✅ **Retry automático** hasta 3 intentos
        - ✅ **Sistema de fallback** robusto
        - ✅ **Validación de respuesta** con evidencia
        - ✅ **Observabilidad completa** con trace IDs
        - ✅ **Métricas de rendimiento** integradas
        """)
        
        # Mostrar estadísticas de uso
        st.markdown("### 📊 Estadísticas de Uso")
        
        # Simular algunas métricas (en producción vendrían de una base de datos)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🔄 Consultas Hoy", "156", "+23")
        with col2:
            st.metric("✅ Tasa de Éxito", "94.2%", "+1.2%")
        with col3:
            st.metric("⏱️ Tiempo Promedio", "1.8s", "-0.3s")
        with col4:
            st.metric("🎯 Confianza Promedio", "87.5%", "+5.1%")

if __name__ == "__main__":
    main()