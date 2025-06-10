# Experimento 2: Evaluación Comparativa BM25 vs TF-IDF

## Hipótesis
El algoritmo BM25 superará significativamente a TF-IDF en la búsqueda de información en documentos normativos del MINEDU debido a:
- Mayor sensibilidad a términos raros/específicos en documentos largos
- Mejor manejo de la saturación de términos frecuentes
- Penalización más efectiva para documentos largos
- Mayor precisión en consultas técnicas con terminología específica

## Metodología Experimental

### Algoritmos Comparados
1. **TF-IDF (Baseline)**
   - Implementación: scikit-learn TfidfVectorizer
   - Configuración: Parámetros por defecto
   - Búsqueda: Similitud coseno con NearestNeighbors

2. **BM25 (Propuesto)**
   - Implementación: rank-bm25 BM25Okapi
   - Configuración: k1=1.5, b=0.75 (ajustados para documentos normativos)
   - Búsqueda: Score BM25 directo

### Dataset de Evaluación
- **Corpus:** Directiva de viáticos MINEDU
- **Preprocesamiento:** Idéntico al sistema actual (limpieza, chunking)
- **Formato:** chunks_v2.json (compartido entre ambos sistemas)

### Consultas de Prueba
Se utilizarán 20 consultas representativas divididas en categorías:
- Consultas sobre montos específicos
- Consultas sobre procedimientos administrativos
- Consultas sobre plazos y fechas
- Consultas semánticas generales

### Métricas de Evaluación
1. **Precisión@k** (k=1,3,5,10)
2. **Recall@k** (k=1,3,5,10)
3. **F1-score**
4. **Mean Reciprocal Rank (MRR)**
5. **Normalized Discounted Cumulative Gain (NDCG)**
6. **Tiempo de respuesta**

## Variables y Controles
- **Variable independiente:** Algoritmo de búsqueda (TF-IDF vs BM25)
- **Variables controladas:** Dataset, preprocesamiento, consultas
- **Variables dependientes:** Métricas de evaluación

## Protocolo Experimental
1. Generar vectorstore con ambos algoritmos usando el mismo conjunto de datos
2. Ejecutar las mismas consultas en ambos sistemas
3. Registrar resultados para cada consulta y sistema
4. Calcular métricas agregadas
5. Realizar análisis estadístico de significancia
6. Documentar hallazgos y limitaciones

## Resultados Esperados
- BM25 superará a TF-IDF en 15-20% en precisión general
- BM25 mostrará mayor ventaja en consultas técnicas específicas
- TF-IDF podría mantener ventajas en consultas muy generales
- BM25 tendrá mejor rendimiento en documentos de longitud variable

## Análisis Posterior
- Identificación de casos donde cada algoritmo es superior
- Evaluación de la viabilidad de un sistema híbrido
- Recomendaciones para optimización de parámetros
- Limitaciones encontradas y posibles soluciones

## Implicaciones para el Sistema Final
- Decisión sobre adopción de BM25 como reemplazo o complemento
- Estrategia para integración con componentes semánticos futuros
- Recomendaciones para ajuste de parámetros en producción
