"""
Visualizaciones interactivas avanzadas para el sistema RAG MINEDU
Usando Plotly, Altair y componentes Streamlit nativos
"""
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

# Visualización
try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    import altair as alt
    ALTAIR_AVAILABLE = True
except ImportError:
    ALTAIR_AVAILABLE = False

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

# Para análisis de datos
try:
    import seaborn as sns
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

logger = logging.getLogger(__name__)

class AdvancedRAGVisualizer:
    """
    Sistema de visualizaciones avanzadas para el RAG MINEDU
    Genera dashboards interactivos con métricas del sistema
    """
    
    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or Path("data")
        
        # Configuración de colores MINEDU
        self.minedu_colors = {
            "primary": "#1f4e79",      # Azul MINEDU
            "secondary": "#2980b9",    # Azul claro
            "accent": "#e74c3c",       # Rojo para alertas
            "success": "#27ae60",      # Verde para éxito
            "warning": "#f39c12",      # Naranja para advertencias
            "info": "#3498db",         # Azul información
            "light": "#ecf0f1",        # Gris claro
            "dark": "#2c3e50"          # Gris oscuro
        }
        
        # Configurar Altair si está disponible
        if ALTAIR_AVAILABLE:
            alt.data_transformers.enable('json')
        
        logger.info("📊 AdvancedRAGVisualizer inicializado")
    
    def create_consultation_dashboard(self, 
                                    consultation_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Crear dashboard principal de consultas
        
        Args:
            consultation_data: Lista de consultas con metadatos
            
        Returns:
            Dict con componentes del dashboard
        """
        if not consultation_data:
            return {"error": "No hay datos de consultas disponibles"}
        
        df = pd.DataFrame(consultation_data)
        
        dashboard = {
            "metrics_overview": self._create_metrics_overview(df),
            "temporal_trends": self._create_temporal_trends(df),
            "query_patterns": self._create_query_patterns(df),
            "performance_metrics": self._create_performance_metrics(df),
            "source_analysis": self._create_source_analysis(df),
            "user_behavior": self._create_user_behavior(df)
        }
        
        return dashboard
    
    def _create_metrics_overview(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Crear overview de métricas principales"""
        try:
            total_queries = len(df)
            avg_response_time = df['response_time'].mean() if 'response_time' in df.columns else 0
            avg_confidence = df['confidence'].mean() if 'confidence' in df.columns else 0
            success_rate = (df['success'] == True).mean() if 'success' in df.columns else 1.0
            
            # Crear métricas cards
            metrics = {
                "total_consultas": {
                    "value": total_queries,
                    "delta": self._calculate_delta(df, 'daily_count') if 'daily_count' in df.columns else None,
                    "format": "number"
                },
                "tiempo_respuesta_promedio": {
                    "value": avg_response_time,
                    "delta": None,
                    "format": "duration",
                    "unit": "segundos"
                },
                "confianza_promedio": {
                    "value": avg_confidence,
                    "delta": None,
                    "format": "percentage"
                },
                "tasa_exito": {
                    "value": success_rate,
                    "delta": None,
                    "format": "percentage"
                }
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error creando overview de métricas: {e}")
            return {"error": str(e)}
    
    def _create_temporal_trends(self, df: pd.DataFrame) -> Optional[go.Figure]:
        """Crear gráfico de tendencias temporales"""
        if not PLOTLY_AVAILABLE:
            return None
        
        try:
            # Preparar datos temporales
            if 'timestamp' in df.columns:
                df['date'] = pd.to_datetime(df['timestamp']).dt.date
                daily_stats = df.groupby('date').agg({
                    'query': 'count',
                    'response_time': 'mean',
                    'confidence': 'mean'
                }).reset_index()
                
                # Crear subplots
                fig = make_subplots(
                    rows=3, cols=1,
                    subplot_titles=['Consultas por Día', 'Tiempo de Respuesta Promedio', 'Confianza Promedio'],
                    vertical_spacing=0.08
                )
                
                # Consultas por día
                fig.add_trace(
                    go.Scatter(
                        x=daily_stats['date'],
                        y=daily_stats['query'],
                        mode='lines+markers',
                        name='Consultas',
                        line=dict(color=self.minedu_colors['primary'])
                    ),
                    row=1, col=1
                )
                
                # Tiempo de respuesta
                fig.add_trace(
                    go.Scatter(
                        x=daily_stats['date'],
                        y=daily_stats['response_time'],
                        mode='lines+markers',
                        name='Tiempo (s)',
                        line=dict(color=self.minedu_colors['warning'])
                    ),
                    row=2, col=1
                )
                
                # Confianza
                fig.add_trace(
                    go.Scatter(
                        x=daily_stats['date'],
                        y=daily_stats['confidence'],
                        mode='lines+markers',
                        name='Confianza',
                        line=dict(color=self.minedu_colors['success'])
                    ),
                    row=3, col=1
                )
                
                fig.update_layout(
                    height=600,
                    title_text="Tendencias Temporales del Sistema",
                    showlegend=False
                )
                
                return fig
            
        except Exception as e:
            logger.error(f"Error creando tendencias temporales: {e}")
            return None
    
    def _create_query_patterns(self, df: pd.DataFrame) -> Optional[go.Figure]:
        """Crear análisis de patrones de consultas"""
        if not PLOTLY_AVAILABLE:
            return None
        
        try:
            # Análisis de categorías de consultas
            query_categories = self._categorize_queries(df['query'].tolist() if 'query' in df.columns else [])
            
            if query_categories:
                categories_df = pd.DataFrame(list(query_categories.items()), 
                                           columns=['Categoría', 'Cantidad'])
                
                # Gráfico de barras horizontal
                fig = go.Figure(data=[
                    go.Bar(
                        y=categories_df['Categoría'],
                        x=categories_df['Cantidad'],
                        orientation='h',
                        marker_color=self.minedu_colors['secondary']
                    )
                ])
                
                fig.update_layout(
                    title="Categorías de Consultas Más Frecuentes",
                    xaxis_title="Número de Consultas",
                    yaxis_title="Categoría",
                    height=400
                )
                
                return fig
            
        except Exception as e:
            logger.error(f"Error creando patrones de consultas: {e}")
            return None
    
    def _create_performance_metrics(self, df: pd.DataFrame) -> Optional[go.Figure]:
        """Crear gráfico de métricas de performance"""
        if not PLOTLY_AVAILABLE:
            return None
        
        try:
            # Scatter plot: Tiempo de respuesta vs Confianza
            if 'response_time' in df.columns and 'confidence' in df.columns:
                fig = go.Figure(data=go.Scatter(
                    x=df['response_time'],
                    y=df['confidence'],
                    mode='markers',
                    marker=dict(
                        size=8,
                        color=df['confidence'] if 'confidence' in df.columns else 'blue',
                        colorscale='Viridis',
                        showscale=True,
                        colorbar=dict(title="Confianza")
                    ),
                    text=df['query'].str[:50] + '...' if 'query' in df.columns else None,
                    hovertemplate='<b>Tiempo:</b> %{x:.2f}s<br><b>Confianza:</b> %{y:.2f}<br><b>Query:</b> %{text}<extra></extra>'
                ))
                
                fig.update_layout(
                    title="Relación Tiempo de Respuesta vs Confianza",
                    xaxis_title="Tiempo de Respuesta (segundos)",
                    yaxis_title="Nivel de Confianza",
                    height=400
                )
                
                return fig
            
        except Exception as e:
            logger.error(f"Error creando métricas de performance: {e}")
            return None
    
    def _create_source_analysis(self, df: pd.DataFrame) -> Optional[go.Figure]:
        """Crear análisis de fuentes más citadas"""
        if not PLOTLY_AVAILABLE:
            return None
        
        try:
            # Extraer fuentes de las respuestas
            sources_list = []
            if 'sources' in df.columns:
                for sources in df['sources']:
                    if isinstance(sources, list):
                        for source in sources:
                            if isinstance(source, dict) and 'source' in source:
                                sources_list.append(source['source'])
            
            if sources_list:
                sources_count = pd.Series(sources_list).value_counts().head(10)
                
                # Gráfico de pie
                fig = go.Figure(data=[go.Pie(
                    labels=sources_count.index,
                    values=sources_count.values,
                    hole=0.4,
                    marker_colors=px.colors.qualitative.Set3
                )])
                
                fig.update_layout(
                    title="Fuentes Normativas Más Citadas",
                    height=400
                )
                
                return fig
            
        except Exception as e:
            logger.error(f"Error creando análisis de fuentes: {e}")
            return None
    
    def _create_user_behavior(self, df: pd.DataFrame) -> Optional[go.Figure]:
        """Crear análisis de comportamiento de usuarios"""
        if not PLOTLY_AVAILABLE:
            return None
        
        try:
            # Histograma de longitud de consultas
            if 'query' in df.columns:
                query_lengths = df['query'].str.len()
                
                fig = go.Figure(data=[go.Histogram(
                    x=query_lengths,
                    nbinsx=20,
                    marker_color=self.minedu_colors['info']
                )])
                
                fig.update_layout(
                    title="Distribución de Longitud de Consultas",
                    xaxis_title="Número de Caracteres",
                    yaxis_title="Frecuencia",
                    height=400
                )
                
                return fig
            
        except Exception as e:
            logger.error(f"Error creando análisis de comportamiento: {e}")
            return None
    
    def create_normative_network_viz(self, 
                                    concordance_data: Dict[str, Any]) -> Optional[go.Figure]:
        """Crear visualización de red normativa"""
        if not PLOTLY_AVAILABLE:
            return None
        
        try:
            # Crear red de relaciones entre normas
            nodes = []
            edges = []
            
            # Extraer nodos (normas)
            if 'central_norms' in concordance_data:
                for i, norm_data in enumerate(concordance_data['central_norms'][:20]):
                    nodes.append({
                        'id': i,
                        'name': norm_data['norm'][:30] + '...',
                        'references': norm_data['references'],
                        'size': min(norm_data['references'] * 5 + 10, 50)
                    })
            
            # Crear layout circular para los nodos
            n_nodes = len(nodes)
            if n_nodes > 0:
                angles = np.linspace(0, 2*np.pi, n_nodes, endpoint=False)
                x_nodes = np.cos(angles)
                y_nodes = np.sin(angles)
                
                # Crear scatter plot para nodos
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=x_nodes,
                    y=y_nodes,
                    mode='markers+text',
                    marker=dict(
                        size=[node['size'] for node in nodes],
                        color=[node['references'] for node in nodes],
                        colorscale='Viridis',
                        showscale=True,
                        colorbar=dict(title="Referencias")
                    ),
                    text=[node['name'] for node in nodes],
                    textposition="middle center",
                    hovertemplate='<b>%{text}</b><br>Referencias: %{marker.color}<extra></extra>'
                ))
                
                fig.update_layout(
                    title="Red de Referencias Normativas",
                    showlegend=False,
                    height=600,
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                )
                
                return fig
            
        except Exception as e:
            logger.error(f"Error creando visualización de red: {e}")
            return None
    
    def create_coverage_heatmap(self, 
                               coverage_data: Dict[str, Any]) -> Optional[go.Figure]:
        """Crear heatmap de cobertura normativa"""
        if not PLOTLY_AVAILABLE:
            return None
        
        try:
            if 'detailed_metrics' in coverage_data:
                metrics = coverage_data['detailed_metrics']
                
                # Preparar datos para heatmap
                norms = [m['norm_name'][:20] + '...' for m in metrics[:20]]
                semantic_coverage = [m['semantic_coverage'] for m in metrics[:20]]
                query_coverage = [m['query_coverage'] for m in metrics[:20]]
                
                # Crear matriz para heatmap
                coverage_matrix = np.array([semantic_coverage, query_coverage])
                
                fig = go.Figure(data=go.Heatmap(
                    z=coverage_matrix,
                    x=norms,
                    y=['Cobertura Semántica', 'Cobertura por Queries'],
                    colorscale='RdYlGn',
                    text=coverage_matrix,
                    texttemplate="%{text:.2f}",
                    textfont={"size": 10}
                ))
                
                fig.update_layout(
                    title="Mapa de Calor - Cobertura Normativa",
                    height=400
                )
                
                return fig
            
        except Exception as e:
            logger.error(f"Error creando heatmap de cobertura: {e}")
            return None
    
    def create_real_time_metrics(self, 
                                recent_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Crear métricas en tiempo real"""
        try:
            if not recent_data:
                return {"error": "No hay datos recientes"}
            
            df = pd.DataFrame(recent_data)
            
            # Métricas de los últimos 5 minutos
            now = datetime.now()
            last_5min = now - timedelta(minutes=5)
            
            if 'timestamp' in df.columns:
                df['datetime'] = pd.to_datetime(df['timestamp'])
                recent_df = df[df['datetime'] >= last_5min]
            else:
                recent_df = df.tail(10)  # Últimas 10 consultas
            
            metrics = {
                "consultas_recientes": len(recent_df),
                "tiempo_promedio_actual": recent_df['response_time'].mean() if 'response_time' in recent_df.columns else 0,
                "confianza_actual": recent_df['confidence'].mean() if 'confidence' in recent_df.columns else 0,
                "errores_recientes": (recent_df['success'] == False).sum() if 'success' in recent_df.columns else 0,
                "ultima_actualizacion": now.strftime("%H:%M:%S")
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error creando métricas tiempo real: {e}")
            return {"error": str(e)}
    
    def _categorize_queries(self, queries: List[str]) -> Dict[str, int]:
        """Categorizar consultas por patrones"""
        categories = {
            "Viáticos y Gastos": 0,
            "Procedimientos": 0,
            "Montos y Límites": 0,
            "Requisitos": 0,
            "Plazos": 0,
            "Autorizaciones": 0,
            "Otros": 0
        }
        
        patterns = {
            "Viáticos y Gastos": [r"viático", r"gasto", r"alimentación", r"hospedaje"],
            "Procedimientos": [r"procedimiento", r"proceso", r"cómo", r"pasos"],
            "Montos y Límites": [r"monto", r"máximo", r"mínimo", r"s/", r"límite"],
            "Requisitos": [r"requisito", r"documento", r"necesario", r"requerir"],
            "Plazos": [r"plazo", r"tiempo", r"día", r"fecha", r"vencimiento"],
            "Autorizaciones": [r"autorización", r"aprobación", r"permiso", r"visto bueno"]
        }
        
        for query in queries:
            query_lower = query.lower()
            categorized = False
            
            for category, pattern_list in patterns.items():
                if any(re.search(pattern, query_lower) for pattern in pattern_list):
                    categories[category] += 1
                    categorized = True
                    break
            
            if not categorized:
                categories["Otros"] += 1
        
        return categories
    
    def _calculate_delta(self, df: pd.DataFrame, column: str) -> Optional[float]:
        """Calcular delta comparando con período anterior"""
        try:
            if len(df) < 2:
                return None
            
            current = df[column].iloc[-1]
            previous = df[column].iloc[-2]
            
            if previous == 0:
                return None
            
            delta = ((current - previous) / previous) * 100
            return delta
            
        except Exception:
            return None
    
    def create_streamlit_dashboard(self, data: Dict[str, Any]) -> None:
        """Crear dashboard completo en Streamlit"""
        if not STREAMLIT_AVAILABLE:
            logger.error("Streamlit no está disponible")
            return
        
        try:
            # Header del dashboard
            st.title("📊 Dashboard RAG MINEDU - Análisis Avanzado")
            st.markdown("---")
            
            # Métricas principales en columnas
            col1, col2, col3, col4 = st.columns(4)
            
            if 'metrics_overview' in data:
                metrics = data['metrics_overview']
                
                with col1:
                    st.metric(
                        "Total Consultas",
                        metrics.get('total_consultas', {}).get('value', 0),
                        delta=metrics.get('total_consultas', {}).get('delta')
                    )
                
                with col2:
                    avg_time = metrics.get('tiempo_respuesta_promedio', {}).get('value', 0)
                    st.metric(
                        "Tiempo Promedio",
                        f"{avg_time:.2f}s"
                    )
                
                with col3:
                    confidence = metrics.get('confianza_promedio', {}).get('value', 0)
                    st.metric(
                        "Confianza Promedio",
                        f"{confidence:.1%}"
                    )
                
                with col4:
                    success_rate = metrics.get('tasa_exito', {}).get('value', 0)
                    st.metric(
                        "Tasa de Éxito",
                        f"{success_rate:.1%}"
                    )
            
            # Gráficos en pestañas
            tab1, tab2, tab3, tab4 = st.tabs(["📈 Tendencias", "🔍 Patrones", "⚡ Performance", "🌐 Red Normativa"])
            
            with tab1:
                st.subheader("Tendencias Temporales")
                if 'temporal_trends' in data and data['temporal_trends']:
                    st.plotly_chart(data['temporal_trends'], use_container_width=True)
                else:
                    st.info("No hay datos temporales disponibles")
            
            with tab2:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Categorías de Consultas")
                    if 'query_patterns' in data and data['query_patterns']:
                        st.plotly_chart(data['query_patterns'], use_container_width=True)
                
                with col2:
                    st.subheader("Fuentes Más Citadas")
                    if 'source_analysis' in data and data['source_analysis']:
                        st.plotly_chart(data['source_analysis'], use_container_width=True)
            
            with tab3:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Tiempo vs Confianza")
                    if 'performance_metrics' in data and data['performance_metrics']:
                        st.plotly_chart(data['performance_metrics'], use_container_width=True)
                
                with col2:
                    st.subheader("Comportamiento de Usuarios")
                    if 'user_behavior' in data and data['user_behavior']:
                        st.plotly_chart(data['user_behavior'], use_container_width=True)
            
            with tab4:
                st.subheader("Red de Referencias Normativas")
                if 'network_viz' in data and data['network_viz']:
                    st.plotly_chart(data['network_viz'], use_container_width=True)
                else:
                    st.info("Visualización de red no disponible")
            
        except Exception as e:
            logger.error(f"Error creando dashboard Streamlit: {e}")
            st.error(f"Error creando dashboard: {e}")
    
    def get_visualization_capabilities(self) -> Dict[str, Any]:
        """Obtener capacidades de visualización disponibles"""
        return {
            "plotly_available": PLOTLY_AVAILABLE,
            "altair_available": ALTAIR_AVAILABLE,
            "streamlit_available": STREAMLIT_AVAILABLE,
            "matplotlib_available": MATPLOTLIB_AVAILABLE,
            "features": {
                "consultation_dashboard": True,
                "temporal_trends": PLOTLY_AVAILABLE,
                "query_patterns": PLOTLY_AVAILABLE,
                "performance_metrics": PLOTLY_AVAILABLE,
                "source_analysis": PLOTLY_AVAILABLE,
                "normative_network": PLOTLY_AVAILABLE,
                "coverage_heatmap": PLOTLY_AVAILABLE,
                "real_time_metrics": True,
                "streamlit_integration": STREAMLIT_AVAILABLE
            },
            "color_scheme": self.minedu_colors
        }

# Instancia global
global_visualizer = AdvancedRAGVisualizer()