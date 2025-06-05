# Experimento 5: Escalabilidad con FAISS para 300K Documentos

## Hipótesis
FAISS permitirá mantener la precisión de Sentence Transformers mientras escala a cientos de miles de documentos con:
- Tiempo de búsqueda sub-segundo
- Uso eficiente de memoria
- Precisión equivalente al método no optimizado

## Configuración de Escalabilidad
- **Índice FAISS:** IndexFlatIP para precisión exacta
- **Fallback:** IndexIVFFlat para datasets masivos
- **Batch processing:** Optimización para consultas múltiples

## Métricas de Escalabilidad
- Tiempo de indexación vs número de documentos
- Tiempo de búsqueda vs tamaño del índice
- Uso de memoria vs tamaño del dataset
- Precision@k para diferentes tamaños de corpus

## Diseño Experimental

### 1. Preparación de Datos Escalables
- Generación de datasets sintéticos de diferentes tamaños:
  - 1K documentos (baseline)
  - 10K documentos
  - 100K documentos
  - 300K documentos (objetivo final)
- Mantenimiento de distribución y características similares al dataset real

### 2. Configuraciones de Índice FAISS
- **IndexFlatIP:** Búsqueda exacta (baseline de precisión)
- **IndexIVFFlat:** Búsqueda aproximada con clusters
- **IndexHNSW:** Búsqueda aproximada con grafos jerárquicos
- Parámetros optimizados para cada configuración

### 3. Protocolo de Evaluación
- Medición de tiempos de indexación
- Medición de tiempos de búsqueda (consulta única y batch)
- Monitoreo de uso de memoria
- Comparación de precisión vs método exacto

## Casos de Prueba Específicos
1. **Escalabilidad lineal**
   - Evaluación de crecimiento de tiempo vs tamaño del dataset
   
2. **Compromiso precisión-velocidad**
   - Análisis de trade-off entre precisión y tiempo de respuesta
   
3. **Optimización de parámetros**
   - Determinación de configuraciones óptimas para producción

## Resultados Esperados
- Mantenimiento de >95% de precisión del método exacto
- Reducción de tiempo de búsqueda en 10x o más
- Escalabilidad sub-lineal en memoria y tiempo
- Viabilidad demostrada para corpus de 300K documentos

## Implicaciones para Producción
- Recomendaciones de hardware para despliegue
- Estrategia de actualización incremental del índice
- Configuraciones óptimas según prioridad (velocidad vs precisión)
- Proyección de escalabilidad futura (>1M documentos)
