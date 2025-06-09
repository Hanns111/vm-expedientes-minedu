# Diario de Desarrollo: Inicio Fase 2 - Sentence Transformers

**Fecha:** 2025-06-05  
**Autor:** Equipo MINEDU-IA  
**Fase:** 2 - Sentence Transformers  

## Resumen Ejecutivo

Hoy marcamos oficialmente el inicio de la Fase 2 del proyecto, centrada en la implementación de Sentence Transformers para mejorar la comprensión semántica de consultas normativas. Tras completar exitosamente la Fase 1 (BM25 vs TF-IDF), procedemos ahora a incorporar capacidades semánticas al sistema.

## Objetivos de la Fase 2

1. **Implementar Sentence Transformers**
   - Modelo seleccionado: paraphrase-multilingual-MiniLM-L12-v2
   - Justificación: Soporte nativo para español, tamaño compacto, buen rendimiento en tareas de similitud semántica

2. **Desarrollar Sistema de Búsqueda Semántica**
   - Generación de embeddings para chunks de texto
   - Implementación de búsqueda por similitud coseno
   - Desarrollo de sistema de reranking para mejorar precisión

3. **Comparar Triple Sistema**
   - Evaluación comparativa: TF-IDF vs BM25 vs Sentence Transformers
   - Métricas cuantitativas: precisión, recall, F1, nDCG, tiempo de respuesta
   - Análisis cualitativo: comprensión semántica, manejo de sinónimos, robustez

4. **Documentar Resultados Científicos**
   - Registro detallado de experimentos y resultados
   - Análisis de fortalezas y debilidades de cada enfoque
   - Actualización de documentación científica

## Hipótesis Principal

Nuestra hipótesis es que el sistema basado en Sentence Transformers superará significativamente a los métodos léxicos (TF-IDF y BM25) en términos de comprensión semántica y relevancia de resultados, especialmente para:

1. Consultas que utilizan sinónimos no presentes en los documentos
2. Preguntas formuladas en lenguaje natural vs. términos técnicos exactos
3. Consultas que requieren comprensión contextual

Esperamos una mejora de al menos 10-15% en precisión semántica respecto a BM25, aunque con un costo en tiempo de procesamiento.

## Métricas a Evaluar

| Métrica | Descripción | Objetivo |
|---------|-------------|----------|
| Precisión semántica | Capacidad para entender consultas con variaciones semánticas | >85% |
| Manejo de sinónimos | Capacidad para relacionar términos sinónimos | >80% |
| Tiempo de respuesta | Milisegundos para devolver resultados | <500ms |
| nDCG@5 | Discounted Cumulative Gain normalizado para top 5 resultados | >0.75 |
| Robustez | Rendimiento con consultas mal formuladas o incompletas | >70% |

## Plan de Trabajo

1. **Día 1-2: Implementación Base**
   - Desarrollo de `generate_vectorstore_transformers.py`
   - Desarrollo de `search_vectorstore_transformers.py`
   - Pruebas iniciales con consultas estándar

2. **Día 3-4: Evaluación Comparativa**
   - Desarrollo de `compare_all_systems.py`
   - Ejecución de batería de pruebas con consultas diversas
   - Análisis de resultados preliminares

3. **Día 5-7: Optimización**
   - Ajuste de parámetros del modelo
   - Implementación de técnicas de reranking
   - Mejoras en velocidad de procesamiento

4. **Día 8-10: Documentación y Conclusiones**
   - Análisis detallado de resultados
   - Actualización de documentación científica
   - Preparación para Fase 3 (FAISS)

## Desafíos Anticipados

1. **Rendimiento computacional:** Los modelos de transformers son más intensivos en recursos que BM25
2. **Equilibrio velocidad-precisión:** Necesidad de optimizar para mantener tiempos de respuesta aceptables
3. **Evaluación cualitativa:** Desarrollar métricas objetivas para medir comprensión semántica

## Próximos Pasos Inmediatos

1. Ejecutar: `python src/ai/generate_vectorstore_transformers.py`
2. Ejecutar: `python src/ai/search_vectorstore_transformers.py`
3. Realizar comparación triple: TF-IDF vs BM25 vs Transformers
4. Documentar diferencias semánticas vs léxicas
5. Actualizar diario con resultados iniciales

---

**Nota:** Este diario será actualizado diariamente durante la Fase 2 para registrar progreso, decisiones y resultados.
