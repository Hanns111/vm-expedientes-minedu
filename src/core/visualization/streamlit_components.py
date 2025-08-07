"""
Componentes especializados para Streamlit
Widgets interactivos y visualizaciones avanzadas para el dashboard RAG
"""
import logging
from typing import Dict, Any, List, Optional, Callable
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

try:
    import streamlit as st
    from streamlit_option_menu import option_menu
    from streamlit_autorefresh import st_autorefresh
    from streamlit_echarts import st_echarts
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

logger = logging.getLogger(__name__)

class StreamlitRAGComponents:
    """
    Componentes especializados de Streamlit para el sistema RAG MINEDU
    """
    
    def __init__(self):
        self.minedu_theme = {
            "primary_color": "#1f4e79",
            "background_color": "#ffffff", 
            "secondary_background_color": "#f0f2f6",
            "text_color": "#262730",
            "font": "sans serif"
        }
        
        logger.info("🎨 StreamlitRAGComponents inicializado")
    
    def create_sidebar_navigation(self) -> str:
        """Crear navegación lateral personalizada"""
        with st.sidebar:
            st.image("https://www.gob.pe/assets/logos/gob_pe-30851d0a1eb69d1aaa0700b5b5e73f5b7b0f01746c5a8b3a5a9fa1e0c09b6e85.png", width=200)
            st.markdown("---")
            
            selected = option_menu(
                "Navegación Principal",
                ["🏠 Inicio", "📊 Análisis", "🔍 Consultas", "📈 Métricas", "⚙️ Configuración"],
                icons=['house', 'graph-up', 'search', 'speedometer2', 'gear'],
                menu_icon="cast",
                default_index=0,
                styles={
                    "container": {"padding": "0!important", "background-color": "#fafafa"},
                    "icon": {"color": "#1f4e79", "font-size": "18px"}, 
                    "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
                    "nav-link-selected": {"background-color": "#1f4e79"},
                }
            )
            
            return selected
    
    def create_real_time_metrics_panel(self, 
                                     update_callback: Callable = None,
                                     refresh_interval: int = 30) -> Dict[str, Any]:
        """Panel de métricas en tiempo real con auto-refresh"""
        
        # Auto-refresh cada 30 segundos
        count = st_autorefresh(interval=refresh_interval * 1000, key="metrics_refresh")
        
        st.markdown("### 📊 Métricas en Tiempo Real")
        
        # Obtener datos actualizados
        if update_callback:
            try:
                current_metrics = update_callback()
            except Exception as e:
                st.error(f"Error obteniendo métricas: {e}")
                return {}
        else:
            # Datos mock para demo
            current_metrics = {
                "consultas_activas": np.random.randint(5, 25),
                "tiempo_respuesta": np.random.uniform(0.5, 2.0),
                "confianza_promedio": np.random.uniform(0.7, 0.95),
                "errores_recientes": np.random.randint(0, 3),
                "ultima_actualizacion": datetime.now().strftime("%H:%M:%S")
            }
        
        # Mostrar métricas en columnas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            self._create_metric_card(
                "Consultas Activas",
                current_metrics.get("consultas_activas", 0),
                "👥",
                color="blue"
            )
        
        with col2:
            tiempo = current_metrics.get("tiempo_respuesta", 0)
            color = "green" if tiempo < 1.0 else "orange" if tiempo < 2.0 else "red"
            self._create_metric_card(
                "Tiempo Respuesta",
                f"{tiempo:.2f}s",
                "⚡",
                color=color
            )
        
        with col3:
            confianza = current_metrics.get("confianza_promedio", 0)
            color = "green" if confianza > 0.8 else "orange" if confianza > 0.6 else "red"
            self._create_metric_card(
                "Confianza",
                f"{confianza:.1%}",
                "🎯",
                color=color
            )
        
        with col4:
            errores = current_metrics.get("errores_recientes", 0)
            color = "green" if errores == 0 else "orange" if errores < 3 else "red"
            self._create_metric_card(
                "Errores",
                str(errores),
                "⚠️",
                color=color
            )
        
        # Timestamp de última actualización
        st.caption(f"🔄 Última actualización: {current_metrics.get('ultima_actualizacion', 'N/A')}")
        
        return current_metrics
    
    def _create_metric_card(self, title: str, value: Any, icon: str, color: str = "blue"):
        """Crear tarjeta de métrica personalizada"""
        color_map = {
            "blue": "#1f4e79",
            "green": "#27ae60", 
            "orange": "#f39c12",
            "red": "#e74c3c"
        }
        
        card_color = color_map.get(color, "#1f4e79")
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(90deg, {card_color} 0%, {card_color}dd 100%);
            padding: 1rem;
            border-radius: 0.5rem;
            color: white;
            text-align: center;
            margin: 0.5rem 0;
        ">
            <div style="font-size: 2rem;">{icon}</div>
            <div style="font-size: 1.5rem; font-weight: bold;">{value}</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">{title}</div>
        </div>
        """, unsafe_allow_html=True)
    
    def create_interactive_query_builder(self) -> Dict[str, Any]:
        """Constructor interactivo de consultas"""
        st.markdown("### 🔧 Constructor de Consultas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Plantillas predefinidas
            plantilla = st.selectbox(
                "Plantilla de consulta:",
                [
                    "Personalizada",
                    "¿Cuál es el monto máximo para viáticos de [DESTINO]?",
                    "¿Qué documentos requiero para solicitar [TIPO_GASTO]?", 
                    "¿Cuál es el procedimiento para [ACCION]?",
                    "¿Cuánto tiempo antes debo solicitar [SERVICIO]?"
                ]
            )
            
            # Parámetros dinámicos
            if plantilla != "Personalizada":
                parametros = {}
                if "[DESTINO]" in plantilla:
                    parametros["DESTINO"] = st.text_input("Destino:", placeholder="Lima, Cusco, etc.")
                if "[TIPO_GASTO]" in plantilla:
                    parametros["TIPO_GASTO"] = st.selectbox("Tipo de gasto:", ["viáticos", "pasajes", "hospedaje"])
                if "[ACCION]" in plantilla:
                    parametros["ACCION"] = st.text_input("Acción:", placeholder="solicitar viáticos, aprobar gastos, etc.")
                if "[SERVICIO]" in plantilla:
                    parametros["SERVICIO"] = st.text_input("Servicio:", placeholder="comisión de servicio, viáticos, etc.")
        
        with col2:
            # Configuración avanzada
            st.markdown("**Configuración Avanzada:**")
            
            metodo_busqueda = st.radio(
                "Método de búsqueda:",
                ["Híbrido (Recomendado)", "Semántico", "Lexical (BM25)", "TF-IDF"]
            )
            
            nivel_detalle = st.slider("Nivel de detalle:", 1, 5, 3)
            incluir_fuentes = st.checkbox("Incluir fuentes detalladas", value=True)
            
        # Construir consulta final
        if plantilla == "Personalizada":
            consulta_final = st.text_area("Escribe tu consulta:", height=100)
        else:
            consulta_final = plantilla
            for param, valor in parametros.items() if 'parametros' in locals() else []:
                if valor:
                    consulta_final = consulta_final.replace(f"[{param}]", valor)
        
        # Validar y mostrar consulta
        if consulta_final and not any(f"[{param}]" in consulta_final for param in ["DESTINO", "TIPO_GASTO", "ACCION", "SERVICIO"]):
            st.success("✅ Consulta construida correctamente")
            
            if st.button("🚀 Ejecutar Consulta", type="primary"):
                return {
                    "query": consulta_final,
                    "method": metodo_busqueda,
                    "detail_level": nivel_detalle,
                    "include_sources": incluir_fuentes,
                    "ready": True
                }
        else:
            st.warning("⚠️ Complete todos los parámetros requeridos")
        
        return {"ready": False}
    
    def create_coverage_analysis_panel(self, coverage_data: Dict[str, Any]):
        """Panel de análisis de cobertura normativa"""
        st.markdown("### 📋 Análisis de Cobertura Normativa")
        
        if not coverage_data:
            st.info("No hay datos de cobertura disponibles")
            return
        
        # Métricas generales de cobertura
        col1, col2, col3 = st.columns(3)
        
        with col1:
            overall_coverage = coverage_data.get('overall_coverage', 0)
            color = "green" if overall_coverage > 0.8 else "orange" if overall_coverage > 0.6 else "red"
            self._create_metric_card(
                "Cobertura General",
                f"{overall_coverage:.1%}",
                "📊",
                color=color
            )
        
        with col2:
            uncovered = coverage_data.get('uncovered_norms', 0)
            total = coverage_data.get('total_norms', 1)
            color = "green" if uncovered == 0 else "orange" if uncovered < total * 0.2 else "red"
            self._create_metric_card(
                "Normas Sin Cobertura",
                f"{uncovered}/{total}",
                "❌",
                color=color
            )
        
        with col3:
            critical_gaps = len(coverage_data.get('critical_gaps', []))
            color = "green" if critical_gaps == 0 else "red"
            self._create_metric_card(
                "Gaps Críticos",
                str(critical_gaps),
                "🚨",
                color=color
            )
        
        # Detalles de gaps críticos
        critical_gaps = coverage_data.get('critical_gaps', [])
        if critical_gaps:
            st.markdown("#### 🚨 Gaps Críticos Detectados")
            for gap in critical_gaps:
                st.error(f"• {gap}")
        
        # Recomendaciones
        recommendations = coverage_data.get('recommendations', [])
        if recommendations:
            st.markdown("#### 💡 Recomendaciones")
            for rec in recommendations:
                st.info(f"• {rec}")
        
        # Tabla de normas con problemas
        if 'detailed_metrics' in coverage_data:
            problematic_norms = [
                m for m in coverage_data['detailed_metrics']
                if m.get('test_status') in ['uncovered', 'partial']
            ]
            
            if problematic_norms:
                st.markdown("#### 📋 Normas que Requieren Atención")
                
                df_problems = pd.DataFrame([
                    {
                        "Norma": norm.get('norm_name', 'N/A')[:30] + '...',
                        "Status": norm.get('test_status', 'N/A'),
                        "Cobertura Semántica": f"{norm.get('semantic_coverage', 0):.1%}",
                        "Queries": norm.get('query_coverage', 0),
                        "Gaps": len(norm.get('gaps_detected', []))
                    }
                    for norm in problematic_norms[:10]
                ])
                
                st.dataframe(df_problems, use_container_width=True)
    
    def create_system_health_monitor(self, system_metrics: Dict[str, Any]):
        """Monitor de salud del sistema"""
        st.markdown("### 💊 Monitor de Salud del Sistema")
        
        # Status general
        overall_health = self._calculate_system_health(system_metrics)
        
        health_color = "green" if overall_health > 0.8 else "orange" if overall_health > 0.6 else "red"
        health_icon = "✅" if overall_health > 0.8 else "⚠️" if overall_health > 0.6 else "❌"
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(90deg, {'#27ae60' if overall_health > 0.8 else '#f39c12' if overall_health > 0.6 else '#e74c3c'} 0%, 
            {'#27ae60dd' if overall_health > 0.8 else '#f39c12dd' if overall_health > 0.6 else '#e74c3cdd'} 100%);
            padding: 1.5rem;
            border-radius: 0.5rem;
            color: white;
            text-align: center;
            margin: 1rem 0;
        ">
            <div style="font-size: 3rem;">{health_icon}</div>
            <div style="font-size: 2rem; font-weight: bold;">Salud del Sistema: {overall_health:.1%}</div>
            <div style="font-size: 1rem; opacity: 0.9;">{'Sistema operativo' if overall_health > 0.8 else 'Requiere atención' if overall_health > 0.6 else 'Estado crítico'}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Componentes individuales
        st.markdown("#### 🔧 Estado de Componentes")
        
        components = {
            "Base de Datos": system_metrics.get('database_health', 1.0),
            "Modelos IA": system_metrics.get('ai_models_health', 1.0),
            "Cache": system_metrics.get('cache_health', 1.0),
            "APIs": system_metrics.get('api_health', 1.0),
            "Vectorstores": system_metrics.get('vectorstore_health', 1.0)
        }
        
        cols = st.columns(len(components))
        
        for i, (component, health) in enumerate(components.items()):
            with cols[i]:
                color = "green" if health > 0.8 else "orange" if health > 0.6 else "red"
                icon = "✅" if health > 0.8 else "⚠️" if health > 0.6 else "❌"
                
                st.markdown(f"""
                <div style="
                    border: 2px solid {'#27ae60' if health > 0.8 else '#f39c12' if health > 0.6 else '#e74c3c'};
                    padding: 1rem;
                    border-radius: 0.5rem;
                    text-align: center;
                    margin: 0.5rem 0;
                ">
                    <div style="font-size: 1.5rem;">{icon}</div>
                    <div style="font-weight: bold;">{component}</div>
                    <div style="color: {'#27ae60' if health > 0.8 else '#f39c12' if health > 0.6 else '#e74c3c'};">{health:.1%}</div>
                </div>
                """, unsafe_allow_html=True)
    
    def create_advanced_search_interface(self) -> Dict[str, Any]:
        """Interfaz de búsqueda avanzada con filtros"""
        st.markdown("### 🔍 Búsqueda Avanzada")
        
        # Query principal
        query = st.text_input(
            "Consulta:",
            placeholder="Ej: ¿Cuál es el monto máximo para viáticos en Lima?",
            help="Escribe tu consulta en lenguaje natural"
        )
        
        with st.expander("⚙️ Filtros Avanzados"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Filtros de fuente
                st.markdown("**Filtros de Fuente:**")
                fuentes = st.multiselect(
                    "Normas específicas:",
                    ["Directiva 011-2020-MINEDU", "Decreto Supremo 007-2020-EF", "Ley 30879", "Todas"],
                    default=["Todas"]
                )
                
                # Filtros temporales
                fecha_desde = st.date_input("Vigente desde:")
                fecha_hasta = st.date_input("Vigente hasta:")
            
            with col2:
                # Filtros de contenido
                st.markdown("**Filtros de Contenido:**")
                categorias = st.multiselect(
                    "Categorías:",
                    ["Viáticos", "Gastos de Viaje", "Procedimientos", "Montos", "Requisitos"],
                    default=[]
                )
                
                # Configuración de búsqueda
                st.markdown("**Configuración:**")
                max_resultados = st.slider("Máximo resultados:", 1, 20, 5)
                umbral_confianza = st.slider("Umbral de confianza:", 0.0, 1.0, 0.6, 0.1)
        
        # Botones de acción
        col1, col2, col3 = st.columns(3)
        
        with col1:
            buscar = st.button("🔍 Buscar", type="primary")
        
        with col2:
            buscar_semantico = st.button("🧠 Búsqueda Semántica")
        
        with col3:
            buscar_exacto = st.button("📝 Búsqueda Exacta")
        
        if any([buscar, buscar_semantico, buscar_exacto]):
            search_params = {
                "query": query,
                "sources": fuentes,
                "date_from": fecha_desde if 'fecha_desde' in locals() else None,
                "date_to": fecha_hasta if 'fecha_hasta' in locals() else None,
                "categories": categorias,
                "max_results": max_resultados,
                "confidence_threshold": umbral_confianza,
                "search_type": "semantic" if buscar_semantico else "exact" if buscar_exacto else "hybrid",
                "execute": True
            }
            return search_params
        
        return {"execute": False}
    
    def _calculate_system_health(self, metrics: Dict[str, Any]) -> float:
        """Calcular salud general del sistema"""
        health_factors = [
            metrics.get('database_health', 1.0),
            metrics.get('ai_models_health', 1.0), 
            metrics.get('cache_health', 1.0),
            metrics.get('api_health', 1.0),
            metrics.get('vectorstore_health', 1.0)
        ]
        
        return sum(health_factors) / len(health_factors)
    
    def create_export_controls(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Controles para exportar datos y reportes"""
        st.markdown("### 📤 Exportar Datos")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Exportar Dashboard", help="Exportar dashboard actual como imagen"):
                return {"action": "export_dashboard", "format": "png"}
        
        with col2:
            if st.button("📈 Exportar Métricas", help="Exportar métricas como CSV"):
                return {"action": "export_metrics", "format": "csv"}
        
        with col3:
            if st.button("📋 Generar Reporte", help="Generar reporte completo en PDF"):
                return {"action": "generate_report", "format": "pdf"}
        
        # Opciones de formato
        with st.expander("⚙️ Opciones de Exportación"):
            formato_data = st.selectbox("Formato de datos:", ["CSV", "Excel", "JSON"])
            incluir_graficos = st.checkbox("Incluir gráficos", value=True)
            periodo = st.selectbox("Período:", ["Último día", "Última semana", "Último mes", "Todos los datos"])
            
            if st.button("✅ Confirmar Exportación"):
                return {
                    "action": "export_custom",
                    "format": formato_data.lower(),
                    "include_charts": incluir_graficos,
                    "period": periodo
                }
        
        return {"action": None}
    
    def get_component_status(self) -> Dict[str, Any]:
        """Estado de disponibilidad de componentes"""
        return {
            "streamlit_available": STREAMLIT_AVAILABLE,
            "plotly_available": PLOTLY_AVAILABLE,
            "components": {
                "sidebar_navigation": STREAMLIT_AVAILABLE,
                "real_time_metrics": STREAMLIT_AVAILABLE,
                "query_builder": STREAMLIT_AVAILABLE,
                "coverage_analysis": STREAMLIT_AVAILABLE,
                "health_monitor": STREAMLIT_AVAILABLE,
                "advanced_search": STREAMLIT_AVAILABLE,
                "export_controls": STREAMLIT_AVAILABLE
            },
            "theme": self.minedu_theme
        }

# Instancia global
global_streamlit_components = StreamlitRAGComponents()