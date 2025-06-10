# Protocolos de Testing Científico

## Consultas de Evaluación Estándar
1. "¿Cuál es el procedimiento para solicitar viáticos?"
2. "¿Cuál es el monto máximo para viáticos?"
3. "¿Qué documentos requiere la solicitud?"
4. "¿Cuánto tiempo antes debo solicitar viáticos?"
5. "¿Quién autoriza los viáticos?"
6. "¿Cómo se rinden los gastos de viáticos?"
7. "¿Cuáles son los plazos para rendición de viáticos?"
8. "¿Qué normativa regula los viáticos?"
9. "¿Qué sucede si no rindo mis viáticos a tiempo?"
10. "¿Se pueden solicitar viáticos internacionales?"

## Métricas de Evaluación

### Métricas Cuantitativas
- **Velocidad:** Tiempo de respuesta en segundos
- **Precisión (P@k):** Proporción de resultados relevantes entre los k primeros
- **Recall:** Proporción de documentos relevantes recuperados
- **F1-Score:** Media armónica entre precisión y recall
- **nDCG:** Discounted Cumulative Gain normalizado (considera el orden)
- **MAP:** Mean Average Precision

### Métricas Cualitativas
- **Relevancia:** Pertinencia del resultado para la consulta
- **Coherencia:** Fluidez y cohesión del texto recuperado
- **Completitud:** Grado en que la respuesta cubre todos los aspectos de la consulta
- **Consistencia:** Reproducibilidad entre ejecuciones
- **Robustez:** Manejo de consultas variadas o mal formuladas

## Protocolo de Comparación

### Preparación
1. Asegurar que todos los sistemas usen los mismos datos fuente
2. Verificar que no haya texto corrupto o problemas de OCR
3. Configurar parámetros comparables (top_k, umbrales, etc.)
4. Preparar ambiente de ejecución consistente

### Ejecución
1. Ejecutar misma consulta en todos los sistemas a comparar
2. Registrar tiempo de inicio y fin para cada sistema
3. Capturar resultados completos (no solo el primero)
4. Guardar metadatos de ejecución (timestamp, parámetros)
5. Repetir cada consulta 3 veces para verificar consistencia

### Análisis
1. Calcular métricas cuantitativas para cada sistema
2. Evaluar cualitativamente la relevancia de los resultados
3. Identificar patrones de éxito y fracaso
4. Documentar diferencias cualitativas entre sistemas
5. Calcular significancia estadística de las diferencias

## Herramientas de Evaluación

### Automatizadas
- `compare_tfidf_bm25.py`: Comparación entre sistemas léxicos
- `benchmark_search.py`: Medición de tiempos y recursos
- `relevance_evaluator.py`: Cálculo de métricas de relevancia

### Manuales
- Evaluación por expertos en normativa
- Cuestionarios de satisfacción para usuarios finales
- Análisis de casos de uso específicos

## Documentación de Resultados

### Formato Estándar
```json
{
  "query": "¿Cuál es el procedimiento para solicitar viáticos?",
  "systems": {
    "tfidf": {
      "time": 0.2271,
      "results": [...],
      "metrics": {
        "precision": 0.8,
        "recall": 0.7,
        "f1": 0.75
      }
    },
    "bm25": {
      "time": 0.0051,
      "results": [...],
      "metrics": {
        "precision": 0.8,
        "recall": 0.6,
        "f1": 0.69
      }
    }
  },
  "analysis": {
    "overlap": 0.2,
    "speed_improvement": 97.77,
    "qualitative_notes": "..."
  }
}
```

### Almacenamiento
- Resultados guardados en `data/evaluation/benchmark_results/`
- Formato JSON para análisis posterior
- Informes en Markdown para documentación científica

## Calendario de Evaluación
- **Evaluación Fase 1:** BM25 vs TF-IDF (Completado)
- **Evaluación Fase 2:** Sentence Transformers vs BM25 (Planificado)
- **Evaluación Fase 3:** FAISS vs búsqueda exacta (Planificado)
- **Evaluación Fase 4:** Sistema híbrido vs componentes individuales (Planificado)
- **Evaluación Final:** Sistema completo con usuarios reales (Planificado)
