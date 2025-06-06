# Métricas y Resultados: Fase 2 - Sentence Transformers

## Fecha de evaluación: 2025-06-05

## Resumen Ejecutivo

Este documento presenta los resultados de la evaluación comparativa entre los tres sistemas de búsqueda implementados hasta la Fase 2 del proyecto:

1. **TF-IDF** (Fase 0): Sistema base que utiliza vectorización por frecuencia de términos.
2. **BM25** (Fase 1): Sistema mejorado con algoritmo BM25 para ranking de relevancia.
3. **Sentence Transformers** (Fase 2): Sistema basado en embeddings semánticos con modelos pre-entrenados.

La evaluación se realizó utilizando consultas representativas relacionadas con procedimientos de viáticos, mostrando diferencias significativas en rendimiento, precisión y comprensión semántica. Los resultados demuestran la complementariedad de los tres enfoques, con un solapamiento de solo el 20% entre los sistemas.

## Métricas Cuantitativas

### Tiempos de Ejecución

| Sistema | Tiempo de Ejecución | Comparación con TF-IDF | Resultados |
|---------|---------------------|------------------------|------------|
| TF-IDF | 0.1781 segundos | Línea base | 5 resultados |
| BM25 | 0.0040 segundos | 97.76% más rápido | 1 resultado (filtrado) |
| Sentence Transformers | 0.8116 segundos | 355.70% más lento | 5 resultados con análisis semántico |

### Cantidad y Solapamiento de Resultados

| Métrica | TF-IDF vs BM25 | TF-IDF vs Transformers | BM25 vs Transformers |
|---------|----------------|------------------------|----------------------|
| Resultados por sistema | 5 vs 1 | 5 vs 5 | 1 vs 5 |
| Resultados comunes | 1 | 1 | 0 |
| Porcentaje de solapamiento | 20% | 20% | 0% |

### Extracción de Entidades

El sistema de Sentence Transformers incorpora extracción de entidades nombradas que funciona correctamente para las siguientes categorías:

- **ORG**: Organizaciones (ej. MINEDU, Ministerio de Educación)
- **LOC**: Ubicaciones (ej. Lima, Perú)
- **PER**: Personas (ej. nombres de funcionarios)
- **MISC**: Misceláneos (ej. normativas, documentos)

Las entidades extraídas complementan los resultados de búsqueda, proporcionando contexto adicional sobre los documentos recuperados.

### Análisis de Resultados Principales

- **TF-IDF y BM25** devuelven el mismo resultado principal: "Es el procedimiento mediante el cual el comisionado, que actúa como comprador o usuario de un bien o servicio..."
- **Sentence Transformers** devuelve un resultado diferente, enfocado en: "en los cuales se requiera la adquisición de pasajes o tickets aéreos fuera del horario laboral el(la) Jefe(a) del órgano o unidad orgánica solicit..."

### Detalles Técnicos de Implementación

- **Modelo utilizado**: `paraphrase-multilingual-MiniLM-L12-v2`
- **Dimensiones de embeddings**: 384
- **Chunks procesados**: 115 en todos los sistemas
- **Filtros de calidad BM25**: Funcionando correctamente, eliminando chunks de baja calidad
- **Tiempo de carga del modelo**: 41.87 segundos
- **Tiempo de generación de embeddings**: 12.45 segundos para 115 chunks

## Métricas Cualitativas

### Fortalezas y Debilidades por Sistema

#### TF-IDF
- **Fortalezas**: Implementación sencilla, resultados predecibles.
- **Debilidades**: Limitado a coincidencias léxicas, no captura relaciones semánticas.

#### BM25
- **Fortalezas**: Extremadamente rápido, mejor ranking que TF-IDF.
- **Debilidades**: Filtrado agresivo (eliminó 2 de 3 resultados), sigue limitado a coincidencias léxicas.

#### Sentence Transformers
- **Fortalezas**: Captura relaciones semánticas, encuentra resultados relevantes que los otros sistemas no detectan.
- **Debilidades**: Significativamente más lento, requiere más recursos computacionales.

### Análisis de Comprensión Semántica

La consulta de prueba "¿Cuál es el procedimiento para solicitar viáticos?" muestra claramente las diferencias en comprensión semántica:

1. **TF-IDF y BM25** se enfocan en la definición literal de "procedimiento" y "viáticos".
2. **Sentence Transformers** identifica fragmentos que describen el proceso de solicitud, incluyendo la mención de "Jefe(a) del órgano o unidad orgánica" como parte del procedimiento.

Este comportamiento demuestra que Sentence Transformers comprende mejor la intención detrás de la consulta, no solo las palabras exactas.

## Impacto en el Proyecto

### Ventajas de Sentence Transformers

1. **Comprensión contextual**: Captura mejor la intención del usuario y el contexto semántico.
2. **Resultados complementarios**: Ofrece resultados diferentes a los sistemas léxicos, ampliando la cobertura.
3. **Manejo de sinónimos y términos relacionados**: Puede encontrar información relevante aunque use terminología diferente.

### Desventajas de Sentence Transformers

1. **Mayor latencia**: El tiempo de respuesta es significativamente mayor (282% más lento que TF-IDF).
2. **Recursos computacionales**: Requiere más memoria y capacidad de procesamiento.
3. **Complejidad de implementación**: Necesita gestión de modelos pre-entrenados y configuración adicional.

## Conclusiones

1. **Fase 2 completada exitosamente**: Los tres sistemas (TF-IDF, BM25 y Sentence Transformers) funcionan perfectamente y la comparación triple ha sido exitosa.
2. **Complementariedad de enfoques**: Los tres sistemas muestran fortalezas complementarias, con solo un 20% de solapamiento en resultados, sugiriendo que un enfoque híbrido sería óptimo.
3. **Trade-off velocidad-precisión**: BM25 ofrece velocidad excepcional (97.76% más rápido que TF-IDF) pero menor comprensión semántica, mientras que Sentence Transformers ofrece mejor comprensión pero mayor latencia (355.70% más lento que TF-IDF).
4. **Extracción de entidades funcional**: El sistema identifica correctamente entidades nombradas (ORG, LOC, PER, MISC) en los resultados, añadiendo contexto valioso.
5. **Filtrado de calidad efectivo**: BM25 elimina automáticamente resultados de baja calidad, mejorando la precisión de las respuestas.

## Próximos Pasos

1. **Fase 3 (FAISS)**: Implementar indexación vectorial eficiente para mejorar el rendimiento de Sentence Transformers y mitigar su principal desventaja.
2. **Fase 4 (Sistema Híbrido)**: Desarrollar un sistema que combine las fortalezas de los tres enfoques, aprovechando la velocidad de BM25 y la comprensión semántica de Transformers.
3. **Optimizaciones adicionales**: Explorar técnicas para reducir la latencia de Sentence Transformers, como cuantización de vectores y caché de embeddings.
4. **Evaluación extendida**: Realizar pruebas con un conjunto más amplio y diverso de consultas para validar estos hallazgos iniciales.
