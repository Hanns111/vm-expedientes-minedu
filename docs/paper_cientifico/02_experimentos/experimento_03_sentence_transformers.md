# Experimento 3: Evaluación de Sentence Transformers para Español Jurídico

## Hipótesis
Los embeddings semánticos de Sentence Transformers superarán significativamente tanto a TF-IDF como a BM25 en:
- Comprensión de contexto semántico
- Manejo de sinónimos y paráfrasis
- Robustez ante variaciones en redacción
- Búsquedas conceptuales (no solo léxicas)

## Modelo Seleccionado
- **Primario:** `paraphrase-multilingual-MiniLM-L12-v2`
- **Backup:** `paraphrase-MiniLM-L6-v2` + traducción
- **Justificación:** Soporte nativo para español, optimizado para paráfrasis

## Variables y Controles
- **Variable independiente:** Método de embedding (BM25 vs Transformers)
- **Variables controladas:** Dataset, preprocessing, métricas
- **Variable dependiente:** Comprensión semántica medida por relevancia

## Casos de Prueba Específicos
- Consultas con sinónimos ("viaje" vs "desplazamiento")
- Consultas conceptuales ("gastos permitidos" vs "¿qué puedo cobrar?")
- Consultas con paráfrasis complejas

## Metodología Experimental
1. **Preparación de Datos**
   - Utilizar el mismo conjunto de chunks que en experimentos anteriores
   - Generar embeddings con el modelo de Sentence Transformers
   - Almacenar vectorstore optimizado

2. **Configuración del Modelo**
   - Modelo base: paraphrase-multilingual-MiniLM-L12-v2
   - Dimensionalidad: 384
   - Normalización: L2
   - Batch size: 32

3. **Evaluación**
   - Comparación directa con TF-IDF y BM25 en las mismas consultas
   - Evaluación adicional con consultas específicamente semánticas
   - Análisis de robustez ante variaciones lingüísticas

## Métricas de Evaluación
- **Precisión semántica:** Capacidad para capturar significado más allá de coincidencias léxicas
- **Robustez:** Consistencia ante variaciones en la formulación de consultas
- **Recall semántico:** Capacidad para recuperar información relevante sin coincidencias exactas
- **Tiempo de procesamiento:** Comparación de eficiencia computacional

## Resultados Esperados
- Mejora del 25-30% sobre TF-IDF en consultas semánticas
- Superioridad clara sobre BM25 en consultas con paráfrasis
- Mayor consistencia en resultados ante variaciones en consultas
- Posible desventaja en tiempo de procesamiento

## Limitaciones Anticipadas
- Mayor costo computacional
- Dependencia de modelos pre-entrenados
- Posible pérdida de precisión en términos técnicos muy específicos
- Necesidad de ajuste para dominio jurídico-administrativo
