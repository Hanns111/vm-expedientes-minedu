"""
Visualización profesional de workflows LangGraph
Genera diagramas Mermaid y Graphviz para análisis y documentación
"""
import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import logging

# Imports para visualización
try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

logger = logging.getLogger(__name__)

class LangGraphVisualizer:
    """Visualizador profesional para workflows LangGraph"""
    
    def __init__(self, output_dir: str = "visualization_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Configuración de colores para diferentes tipos de nodos
        self.node_colors = {
            "input_validation": "#e1f5fe",
            "detect_intent": "#f3e5f5", 
            "route_to_agent": "#e8f5e8",
            "execute_agent": "#fff3e0",
            "validate_response": "#e0f2f1",
            "fallback_legacy": "#ffebee",
            "compose_response": "#e8f5e8",
            "error_handler": "#ffcdd2",
            "start": "#c8e6c9",
            "end": "#ffccbc"
        }
        
        self.edge_colors = {
            "success": "#4caf50",
            "retry": "#ff9800", 
            "fallback": "#f44336",
            "error": "#d32f2f",
            "default": "#666666"
        }
    
    def generate_mermaid_diagram(self, workflow_data: Dict[str, Any] = None) -> str:
        """Generar diagrama Mermaid del workflow"""
        
        mermaid_code = """
graph TD
    A[Input Validation] --> B[Detect Intent]
    B --> C[Route to Agent]
    C --> D[Execute Agent]
    D --> E{Agent Success?}
    E -->|Success| F[Validate Response]
    E -->|Error| G{Max Attempts?}
    G -->|Retry| D
    G -->|Max Reached| H[Error Handler]
    F --> I{Response Valid?}
    I -->|Valid| J[Compose Response]
    I -->|Invalid| K{Can Fallback?}
    K -->|Yes| L[Fallback Legacy]
    K -->|No| H
    L --> M{Fallback Success?}
    M -->|Success| J
    M -->|Failed| H
    J --> N[End]
    H --> O[Error Response]
    O --> N
    
    %% Estilos de nodos
    classDef validation fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
    classDef intent fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef routing fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef execution fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef validation_resp fill:#e0f2f1,stroke:#00695c,stroke-width:2px
    classDef fallback fill:#ffebee,stroke:#d32f2f,stroke-width:2px
    classDef compose fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef error fill:#ffcdd2,stroke:#c62828,stroke-width:2px
    classDef decision fill:#fff9c4,stroke:#f9a825,stroke-width:2px
    classDef terminal fill:#f5f5f5,stroke:#424242,stroke-width:3px
    
    class A validation
    class B intent
    class C routing
    class D execution
    class F validation_resp
    class L fallback
    class J compose
    class H,O error
    class E,G,I,K,M decision
    class N terminal
"""
        
        # Agregar información de trace si está disponible
        if workflow_data and 'node_history' in workflow_data:
            mermaid_code += f"""
    
    %% Información del último trace
    %% Trace ID: {workflow_data.get('trace_id', 'N/A')}
    %% Nodos ejecutados: {', '.join(workflow_data['node_history'])}
    %% Tiempo total: {workflow_data.get('processing_time', 0):.2f}s
"""
        
        return mermaid_code
    
    def generate_graphviz_diagram(self, workflow_data: Dict[str, Any] = None) -> Optional[str]:
        """Generar diagrama Graphviz del workflow"""
        
        if not GRAPHVIZ_AVAILABLE:
            logger.warning("Graphviz no disponible. Instalar con: pip install graphviz")
            return None
        
        # Crear el grafo
        dot = graphviz.Digraph(
            name='langgraph_workflow',
            comment='LangGraph Professional Workflow',
            format='png'
        )
        
        # Configuración del grafo
        dot.attr(rankdir='TB', size='12,16', dpi='300')
        dot.attr('node', shape='box', style='rounded,filled', fontname='Arial')
        dot.attr('edge', fontname='Arial', fontsize='10')
        
        # Nodos del workflow
        nodes = [
            ('start', 'START', self.node_colors['start']),
            ('input_validation', 'Input\\nValidation', self.node_colors['input_validation']),
            ('detect_intent', 'Detect\\nIntent', self.node_colors['detect_intent']),
            ('route_to_agent', 'Route to\\nAgent', self.node_colors['route_to_agent']),
            ('execute_agent', 'Execute\\nAgent', self.node_colors['execute_agent']),
            ('validate_response', 'Validate\\nResponse', self.node_colors['validate_response']),
            ('fallback_legacy', 'Fallback\\nLegacy', self.node_colors['fallback_legacy']),
            ('compose_response', 'Compose\\nResponse', self.node_colors['compose_response']),
            ('error_handler', 'Error\\nHandler', self.node_colors['error_handler']),
            ('end', 'END', self.node_colors['end'])
        ]
        
        # Agregar nodos
        for node_id, label, color in nodes:
            dot.node(node_id, label, fillcolor=color)
        
        # Nodos de decisión (rombos)
        decisions = [
            ('decision_agent', 'Agent\\nSuccess?'),
            ('decision_attempts', 'Max\\nAttempts?'),
            ('decision_validation', 'Response\\nValid?'),
            ('decision_fallback', 'Can\\nFallback?')
        ]
        
        for node_id, label in decisions:
            dot.node(node_id, label, shape='diamond', fillcolor='#fff9c4')
        
        # Edges del workflow
        edges = [
            ('start', 'input_validation', 'start', self.edge_colors['default']),
            ('input_validation', 'detect_intent', 'next', self.edge_colors['success']),
            ('detect_intent', 'route_to_agent', 'next', self.edge_colors['success']),
            ('route_to_agent', 'execute_agent', 'next', self.edge_colors['success']),
            ('execute_agent', 'decision_agent', 'next', self.edge_colors['default']),
            ('decision_agent', 'validate_response', 'success', self.edge_colors['success']),
            ('decision_agent', 'decision_attempts', 'error', self.edge_colors['error']),
            ('decision_attempts', 'execute_agent', 'retry', self.edge_colors['retry']),
            ('decision_attempts', 'error_handler', 'max reached', self.edge_colors['error']),
            ('validate_response', 'decision_validation', 'next', self.edge_colors['default']),
            ('decision_validation', 'compose_response', 'valid', self.edge_colors['success']),
            ('decision_validation', 'decision_fallback', 'invalid', self.edge_colors['fallback']),
            ('decision_fallback', 'fallback_legacy', 'yes', self.edge_colors['fallback']),
            ('decision_fallback', 'error_handler', 'no', self.edge_colors['error']),
            ('fallback_legacy', 'compose_response', 'success', self.edge_colors['success']),
            ('compose_response', 'end', 'complete', self.edge_colors['success']),
            ('error_handler', 'end', 'error', self.edge_colors['error'])
        ]
        
        # Agregar edges
        for source, target, label, color in edges:
            dot.edge(source, target, label=label, color=color, fontcolor=color)
        
        # Resaltar nodos ejecutados si hay información de trace
        if workflow_data and 'node_history' in workflow_data:
            executed_nodes = workflow_data['node_history']
            for node_id in executed_nodes:
                if node_id in [n[0] for n in nodes]:
                    # Agregar borde más grueso a nodos ejecutados
                    dot.node(node_id, style='rounded,filled,bold', penwidth='3')
        
        # Guardar diagrama
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"langgraph_workflow_{timestamp}"
        
        try:
            dot.render(str(output_file), cleanup=True)
            logger.info(f"Diagrama Graphviz guardado en: {output_file}.png")
            return f"{output_file}.png"
        except Exception as e:
            logger.error(f"Error generando diagrama Graphviz: {e}")
            return None
    
    def generate_execution_trace(self, trace_data: Dict[str, Any]) -> str:
        """Generar visualización de trace de ejecución"""
        
        if not trace_data.get('node_history'):
            return "No hay información de trace disponible"
        
        trace_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>LangGraph Execution Trace</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .trace-header {{ background: #1f4e79; color: white; padding: 15px; border-radius: 5px; }}
        .trace-step {{ margin: 10px 0; padding: 10px; border-left: 4px solid #2196f3; background: #f5f5f5; }}
        .trace-step.error {{ border-left-color: #f44336; background: #ffebee; }}
        .trace-step.success {{ border-left-color: #4caf50; background: #e8f5e8; }}
        .trace-step.warning {{ border-left-color: #ff9800; background: #fff3e0; }}
        .trace-meta {{ font-size: 0.9em; color: #666; margin-top: 5px; }}
        .trace-summary {{ background: #e3f2fd; padding: 15px; border-radius: 5px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="trace-header">
        <h1>🔍 LangGraph Execution Trace</h1>
        <p><strong>Trace ID:</strong> {trace_data.get('trace_id', 'N/A')}</p>
        <p><strong>Query:</strong> {trace_data.get('query', 'N/A')}</p>
        <p><strong>Timestamp:</strong> {trace_data.get('timestamp', 'N/A')}</p>
    </div>
    
    <h2>📋 Execution Steps</h2>
"""
        
        # Agregar cada paso del trace
        node_history = trace_data.get('node_history', [])
        for i, node in enumerate(node_history, 1):
            step_class = "trace-step"
            
            # Determinar el tipo de paso para colorear
            if 'error' in node.lower():
                step_class += " error"
            elif 'fallback' in node.lower():
                step_class += " warning"
            elif 'compose' in node.lower() or 'end' in node.lower():
                step_class += " success"
            
            trace_html += f"""
    <div class="{step_class}">
        <strong>Step {i}:</strong> {node.replace('_', ' ').title()}
        <div class="trace-meta">Node: {node}</div>
    </div>
"""
        
        # Resumen del trace
        processing_time = trace_data.get('processing_time', 0)
        used_fallback = trace_data.get('used_fallback', False)
        validation_errors = trace_data.get('validation_errors', [])
        
        trace_html += f"""
    <div class="trace-summary">
        <h3>📊 Execution Summary</h3>
        <ul>
            <li><strong>Total Steps:</strong> {len(node_history)}</li>
            <li><strong>Processing Time:</strong> {processing_time:.2f} seconds</li>
            <li><strong>Used Fallback:</strong> {'Yes' if used_fallback else 'No'}</li>
            <li><strong>Validation Errors:</strong> {len(validation_errors)}</li>
            <li><strong>Final Status:</strong> {'Success' if not validation_errors else 'Warning'}</li>
        </ul>
    </div>
    
    <div class="trace-summary">
        <h3>🔧 Technical Details</h3>
        <pre>{json.dumps(trace_data, indent=2, ensure_ascii=False)}</pre>
    </div>
    
</body>
</html>
"""
        
        # Guardar trace HTML
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        trace_file = self.output_dir / f"execution_trace_{timestamp}.html"
        
        with open(trace_file, 'w', encoding='utf-8') as f:
            f.write(trace_html)
        
        logger.info(f"Trace HTML guardado en: {trace_file}")
        return str(trace_file)
    
    def create_workflow_documentation(self) -> str:
        """Crear documentación completa del workflow"""
        
        doc_content = f"""
# LangGraph Professional Workflow Documentation

Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Overview

Este documento describe el workflow profesional implementado en LangGraph para el sistema RAG de MINEDU.

## Workflow Architecture

### Nodes (Nodos)

1. **Input Validation**
   - Valida y sanitiza la entrada del usuario
   - Detecta contenido malicioso
   - Verifica longitud y formato

2. **Detect Intent**
   - Analiza la intención de la consulta
   - Extrae entidades relevantes
   - Calcula nivel de confianza

3. **Route to Agent**
   - Selecciona el agente apropiado
   - Basado en intención y confianza
   - Fallback a agente por defecto

4. **Execute Agent**
   - Ejecuta la lógica del agente seleccionado
   - Manejo de errores y reintentos
   - Extracción de documentos y evidencia

5. **Validate Response**
   - Valida la calidad de la respuesta
   - Verifica evidencia específica
   - Chequea coherencia y completitud

6. **Fallback Legacy**
   - Sistema de respaldo
   - Respuestas predefinidas
   - Garantiza siempre una respuesta

7. **Compose Response**
   - Construye la respuesta final
   - Agrega metadatos y trazabilidad
   - Formatea para el usuario

8. **Error Handler**
   - Maneja errores críticos
   - Logging detallado
   - Respuesta de error amigable

### Decision Points (Puntos de Decisión)

- **Agent Success**: ¿El agente ejecutó exitosamente?
- **Max Attempts**: ¿Se alcanzó el máximo de intentos?
- **Response Valid**: ¿La respuesta es válida?
- **Can Fallback**: ¿Se puede usar fallback?

### Edge Types (Tipos de Conexión)

- **Success**: Flujo exitoso (verde)
- **Retry**: Reintento necesario (naranja)
- **Fallback**: Activación de fallback (rojo)
- **Error**: Error crítico (rojo oscuro)

## Features Profesionales

### ✅ Validación de Entrada
- Sanitización de HTML/JavaScript
- Verificación de longitud
- Detección de inyección de prompts

### ✅ Sistema de Reintentos
- Hasta 3 intentos automáticos
- Backoff exponencial
- Logging detallado de fallos

### ✅ Fallback Robusto
- Respuestas predefinidas por dominio
- Nunca falla completamente
- Información de contexto

### ✅ Observabilidad Completa
- Trace IDs únicos
- Historial de nodos
- Métricas de rendimiento
- Logs estructurados

### ✅ Validación de Respuesta
- Verificación de evidencia
- Chequeo de fuentes
- Evaluación de completitud

## Configuration

El workflow se configura a través de:

```python
class ProfessionalRAGState(TypedDict):
    messages: Annotated[List, add_messages]
    query: str
    intent: str
    validated_response: bool
    evidence_found: List[str]
    # ... más campos
```

## Usage Example

```python
orchestrator = ProfessionalLangGraphOrchestrator()
result = await orchestrator.process_query_professional("¿Cuál es el monto de viáticos?")
```

## Error Handling

El sistema maneja los siguientes tipos de errores:

1. **Validation Errors**: Entrada inválida
2. **Agent Errors**: Fallos en ejecución
3. **Response Errors**: Respuesta inválida
4. **System Errors**: Errores críticos

## Monitoring

Métricas monitoreadas:

- Tiempo de procesamiento
- Tasa de éxito
- Uso de fallback
- Calidad de respuestas
- Errores por tipo

## Best Practices

1. Siempre usar trace IDs para debugging
2. Monitorear métricas de fallback
3. Revisar logs de validación
4. Optimizar agentes más usados
5. Actualizar respuestas de fallback

"""
        
        # Guardar documentación
        doc_file = self.output_dir / "workflow_documentation.md"
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write(doc_content)
        
        logger.info(f"Documentación guardada en: {doc_file}")
        return str(doc_file)
    
    def generate_metrics_visualization(self, metrics_data: List[Dict[str, Any]]) -> Optional[str]:
        """Generar visualización de métricas"""
        
        if not MATPLOTLIB_AVAILABLE:
            logger.warning("Matplotlib no disponible para visualización de métricas")
            return None
        
        if not metrics_data:
            logger.warning("No hay datos de métricas para visualizar")
            return None
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('LangGraph Professional - Métricas de Rendimiento', fontsize=16)
        
        # Extraer datos
        timestamps = [m.get('timestamp', '') for m in metrics_data]
        processing_times = [m.get('processing_time', 0) for m in metrics_data]
        confidence_scores = [m.get('confidence', 0) for m in metrics_data]
        fallback_usage = [1 if m.get('used_fallback') else 0 for m in metrics_data]
        
        # Gráfico 1: Tiempo de procesamiento
        ax1.plot(range(len(processing_times)), processing_times, 'b-', marker='o')
        ax1.set_title('Tiempo de Procesamiento')
        ax1.set_ylabel('Segundos')
        ax1.set_xlabel('Consultas')
        ax1.grid(True, alpha=0.3)
        
        # Gráfico 2: Scores de confianza
        ax2.hist(confidence_scores, bins=20, alpha=0.7, color='green')
        ax2.set_title('Distribución de Confianza')
        ax2.set_xlabel('Score de Confianza')
        ax2.set_ylabel('Frecuencia')
        ax2.axvline(x=0.8, color='red', linestyle='--', label='Umbral Excelente')
        ax2.legend()
        
        # Gráfico 3: Uso de fallback
        fallback_counts = [sum(fallback_usage[:i+1]) for i in range(len(fallback_usage))]
        ax3.plot(range(len(fallback_counts)), fallback_counts, 'r-', marker='s')
        ax3.set_title('Uso Acumulado de Fallback')
        ax3.set_ylabel('Casos de Fallback')
        ax3.set_xlabel('Consultas')
        ax3.grid(True, alpha=0.3)
        
        # Gráfico 4: Métricas combinadas
        success_rate = [(1 - sum(fallback_usage[:i+1])/(i+1))*100 for i in range(len(fallback_usage))]
        ax4.plot(range(len(success_rate)), success_rate, 'g-', marker='d', label='Tasa de Éxito (%)')
        ax4.set_title('Tasa de Éxito del Sistema')
        ax4.set_ylabel('Porcentaje')
        ax4.set_xlabel('Consultas')
        ax4.set_ylim(0, 100)
        ax4.grid(True, alpha=0.3)
        ax4.legend()
        
        plt.tight_layout()
        
        # Guardar gráfico
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metrics_file = self.output_dir / f"metrics_visualization_{timestamp}.png"
        plt.savefig(metrics_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Visualización de métricas guardada en: {metrics_file}")
        return str(metrics_file)

def create_sample_visualization():
    """Crear visualización de ejemplo"""
    visualizer = LangGraphVisualizer()
    
    # Generar Mermaid
    mermaid_code = visualizer.generate_mermaid_diagram()
    
    # Guardar Mermaid
    mermaid_file = visualizer.output_dir / "workflow_mermaid.md"
    with open(mermaid_file, 'w', encoding='utf-8') as f:
        f.write(f"```mermaid\n{mermaid_code}\n```")
    
    print(f"✅ Diagrama Mermaid guardado en: {mermaid_file}")
    
    # Generar Graphviz si está disponible
    if GRAPHVIZ_AVAILABLE:
        graphviz_file = visualizer.generate_graphviz_diagram()
        if graphviz_file:
            print(f"✅ Diagrama Graphviz guardado en: {graphviz_file}")
    
    # Crear documentación
    doc_file = visualizer.create_workflow_documentation()
    print(f"✅ Documentación guardada en: {doc_file}")
    
    # Ejemplo de trace
    sample_trace = {
        "trace_id": "trace_1234567890",
        "query": "¿Cuál es el monto máximo de viáticos?",
        "timestamp": datetime.now().isoformat(),
        "node_history": ["input_validation", "detect_intent", "route_to_agent", "execute_agent", "validate_response", "compose_response"],
        "processing_time": 1.85,
        "used_fallback": False,
        "validation_errors": []
    }
    
    trace_file = visualizer.generate_execution_trace(sample_trace)
    print(f"✅ Trace HTML guardado en: {trace_file}")
    
    return visualizer

if __name__ == "__main__":
    create_sample_visualization()