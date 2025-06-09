# Plan de Sprint 1.2: Expansión del Dataset y Mejoras en Algoritmos de Búsqueda

**Fecha de inicio:** 8 de junio de 2025  
**Duración estimada:** 2 semanas  
**Fecha de finalización prevista:** 22 de junio de 2025

## 1. Objetivos del Sprint

El Sprint 1.2 se enfoca en expandir el dataset dorado, mejorar los algoritmos de búsqueda existentes e implementar nuevas técnicas de embeddings semánticos. Los objetivos específicos son:

1. **Expandir el dataset dorado** con al menos 30 preguntas adicionales
2. **Optimizar el algoritmo TF-IDF** para una comparación justa con BM25
3. **Implementar Sentence Transformers** para comprensión semántica
4. **Desarrollar un sistema híbrido** que combine BM25 y embeddings semánticos

## 2. Tareas Detalladas

### 2.1 Expansión del Dataset Dorado

| Tarea | Descripción | Prioridad | Estimación |
|-------|-------------|-----------|------------|
| 2.1.1 | Analizar categorías y tipos de consultas actuales | Alta | 1 día |
| 2.1.2 | Identificar categorías subrepresentadas | Alta | 1 día |
| 2.1.3 | Crear 15 preguntas nuevas de tipo factual | Alta | 2 días |
| 2.1.4 | Crear 10 preguntas nuevas de tipo procedural | Alta | 2 días |
| 2.1.5 | Crear 5 preguntas nuevas de tipo reference | Media | 1 día |
| 2.1.6 | Validar respuestas ground truth con expertos | Alta | 2 días |
| 2.1.7 | Actualizar el dataset dorado con las nuevas preguntas | Alta | 1 día |

**Entregable:** Dataset dorado expandido con 50 preguntas en total (20 existentes + 30 nuevas)

### 2.2 Optimización del Algoritmo TF-IDF

| Tarea | Descripción | Prioridad | Estimación |
|-------|-------------|-----------|------------|
| 2.2.1 | Analizar implementación actual de TF-IDF | Alta | 1 día |
| 2.2.2 | Implementar factores de boost similares a BM25 | Alta | 2 días |
| 2.2.3 | Optimizar preprocesamiento de consultas | Media | 1 día |
| 2.2.4 | Implementar normalización por longitud de documento | Alta | 1 día |
| 2.2.5 | Evaluar rendimiento con dataset expandido | Alta | 1 día |

**Entregable:** Algoritmo TF-IDF optimizado con factores de boost y normalización

### 2.3 Implementación de Sentence Transformers

| Tarea | Descripción | Prioridad | Estimación |
|-------|-------------|-----------|------------|
| 2.3.1 | Seleccionar modelo de Sentence Transformers adecuado | Alta | 1 día |
| 2.3.2 | Implementar generación de embeddings | Alta | 2 días |
| 2.3.3 | Crear índice FAISS para búsqueda eficiente | Alta | 1 día |
| 2.3.4 | Implementar búsqueda semántica con Sentence Transformers | Alta | 2 días |
| 2.3.5 | Evaluar rendimiento con dataset expandido | Alta | 1 día |

**Entregable:** Componente de búsqueda semántica basado en Sentence Transformers

### 2.4 Desarrollo de Sistema Híbrido

| Tarea | Descripción | Prioridad | Estimación |
|-------|-------------|-----------|------------|
| 2.4.1 | Diseñar arquitectura del sistema híbrido | Alta | 1 día |
| 2.4.2 | Implementar combinación de resultados BM25 y embeddings | Alta | 2 días |
| 2.4.3 | Desarrollar estrategia de ranking y reordenamiento | Alta | 2 días |
| 2.4.4 | Implementar mecanismo de feedback para mejora continua | Media | 1 día |
| 2.4.5 | Evaluar rendimiento del sistema híbrido | Alta | 1 día |

**Entregable:** Sistema híbrido que combine BM25 y embeddings semánticos

## 3. Métricas de Éxito

Para considerar exitoso el Sprint 1.2, se deben cumplir los siguientes criterios:

1. **Dataset dorado:**
   - Incremento a 50 preguntas totales
   - Cobertura de al menos 6 categorías distintas
   - Distribución equilibrada de tipos de consulta

2. **Algoritmo TF-IDF optimizado:**
   - Mejora de al menos 15% en token_overlap respecto a la versión anterior
   - Tiempo de respuesta comparable a BM25 (±10%)

3. **Sentence Transformers:**
   - token_overlap > 0.5 (mejora respecto a BM25)
   - exact_match > 0.1 (mejora respecto a BM25)

4. **Sistema híbrido:**
   - token_overlap > 0.6 (mejora respecto a los métodos individuales)
   - Capacidad de recuperar información específica en el top-3 de resultados

## 4. Riesgos y Mitigación

| Riesgo | Impacto | Probabilidad | Estrategia de Mitigación |
|--------|---------|--------------|--------------------------|
| Dificultad para encontrar expertos para validar respuestas | Alto | Media | Preparar guías detalladas para validación y considerar validación cruzada entre miembros del equipo |
| Rendimiento insuficiente de Sentence Transformers | Alto | Baja | Tener preparados modelos alternativos y estrategias de fine-tuning |
| Conflictos entre resultados de diferentes algoritmos | Medio | Alta | Diseñar estrategia de ranking robusta con pesos ajustables |
| Expansión insuficiente del dataset | Alto | Baja | Comenzar la expansión del dataset desde el primer día del sprint |

## 5. Dependencias

- Acceso a expertos en normativas del MINEDU para validación
- Recursos computacionales para entrenamiento de modelos
- Instalación de bibliotecas adicionales (sentence-transformers, faiss-cpu)

## 6. Definición de "Terminado"

El Sprint 1.2 se considerará terminado cuando:

1. El dataset dorado contenga 50 preguntas validadas
2. Los algoritmos TF-IDF, BM25 y Sentence Transformers estén implementados y evaluados
3. El sistema híbrido esté funcionando y supere las métricas de éxito definidas
4. La documentación esté actualizada con los resultados y análisis comparativos
5. El código esté versionado con un tag/release para marcar la finalización del Sprint 1.2

---

**Aprobado por:** _________________  
**Fecha de aprobación:** _________________
