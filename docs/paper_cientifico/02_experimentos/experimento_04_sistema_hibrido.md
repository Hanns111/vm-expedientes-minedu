# Experimento 4: Sistema Híbrido BM25 + Sentence Transformers

## Hipótesis
La combinación ponderada de búsqueda léxica (BM25) y semántica (Transformers) superará a cualquier método individual mediante:
- Captura de coincidencias exactas de términos técnicos (BM25)
- Comprensión de intención semántica (Transformers)
- Re-ranking inteligente de resultados combinados

## Metodología de Combinación
- **Scoring híbrido:** α × score_BM25 + (1-α) × score_transformers
- **Optimización de α:** Grid search en [0.1, 0.2, ..., 0.9]
- **Re-ranking:** Top-k de cada método → re-score → ranking final

## Métricas de Evaluación Híbrida
- Mejora sobre mejor método individual
- Consistencia entre tipos de consulta
- Robustez ante consultas ambiguas

## Diseño Experimental
1. **Arquitectura del Sistema Híbrido**
   - Ejecución paralela de búsqueda BM25 y Transformers
   - Normalización de scores para comparabilidad
   - Combinación ponderada con parámetro α optimizable
   - Re-ranking final basado en score combinado

2. **Optimización de Parámetros**
   - Búsqueda en grid para parámetro α
   - Validación cruzada para evitar overfitting
   - Optimización por tipo de consulta

3. **Evaluación Comparativa**
   - Comparación con métodos individuales (TF-IDF, BM25, Transformers)
   - Análisis por categoría de consulta
   - Evaluación de robustez y consistencia

## Casos de Prueba Específicos
1. **Consultas técnicas con terminología específica**
   - Expectativa: BM25 contribuye precisión léxica
   
2. **Consultas conceptuales con variaciones semánticas**
   - Expectativa: Transformers contribuye comprensión semántica
   
3. **Consultas mixtas con componentes léxicos y semánticos**
   - Expectativa: Sistema híbrido muestra superioridad máxima

## Resultados Esperados
- Mejora del 5-10% sobre el mejor método individual
- Mayor consistencia a través de diferentes tipos de consulta
- Robustez mejorada ante variaciones en la formulación
- Precisión cercana al 90% en el dataset de evaluación

## Implicaciones para el Sistema Final
- Determinación del valor óptimo de α para producción
- Estrategia de selección dinámica de α según tipo de consulta
- Arquitectura de sistema para implementación eficiente
- Recomendaciones para escalabilidad con FAISS
