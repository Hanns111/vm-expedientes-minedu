# Diario de Desarrollo: 2025-06-05 - Comparación de Sistemas TF-IDF vs BM25

## Objetivos del Día
- [x] Implementar sistema BM25 paralelo
- [x] Crear comparador para TF-IDF vs BM25
- [x] Ejecutar pruebas comparativas con consultas de prueba
- [x] Documentar resultados y métricas
- [x] Analizar diferencias de rendimiento

## Actividades Realizadas

### 1. Implementación del Comparador Universal
**Descripción:** Se implementó el script `compare_all_systems.py` para ejecutar consultas en múltiples sistemas de búsqueda y generar métricas comparativas detalladas.
**Tiempo invertido:** 2 horas
**Resultados:** Sistema de comparación funcional que genera reportes JSON y muestra resúmenes en consola.
**Problemas encontrados:** Inconsistencias en el formato de resultados entre sistemas.
**Soluciones aplicadas:** Implementación de adaptadores para normalizar formatos de resultados.

### 2. Ejecución de Pruebas Comparativas
**Descripción:** Se ejecutaron consultas de prueba en ambos sistemas para medir diferencias de rendimiento.
**Tiempo invertido:** 1 hora
**Resultados:** Datos comparativos para múltiples consultas de diferentes tipos.
**Problemas encontrados:** Error inicial en el manejo de resultados BM25.
**Soluciones aplicadas:** Corrección del código para manejar correctamente los resultados de diferentes formatos.

## Métricas y Resultados Cuantitativos

### Consulta 1: "¿Cuál es el monto máximo para viáticos nacionales?"
- **Tiempo TF-IDF:** 0.6692 segundos
- **Tiempo BM25:** 0.0020 segundos
- **Mejora en velocidad:** 99.70% más rápido
- **Solapamiento de resultados:** 40.00%
- **Mismo resultado principal:** Sí

### Consulta 2: "Procedimiento para autorización de viajes"
- **Tiempo TF-IDF:** 0.2074 segundos
- **Tiempo BM25:** 0.0011 segundos
- **Mejora en velocidad:** 99.47% más rápido
- **Solapamiento de resultados:** 60.00%
- **Mismo resultado principal:** Sí

### Promedio de Métricas
- **Mejora promedio en velocidad:** 99.58%
- **Solapamiento promedio:** 50.00%
- **Consistencia en resultado principal:** 100%

## Código Creado/Modificado
- `src/ai/compare_all_systems.py`: Implementación del comparador universal
- `docs/paper_cientifico/03_resultados/metricas_cuantitativas.md`: Documentación de métricas
- `docs/paper_cientifico/03_resultados/analisis_cualitativo.md`: Análisis de diferencias

## Hallazgos Técnicos Importantes
1. **Superioridad en velocidad:** BM25 es consistentemente 2 órdenes de magnitud más rápido que TF-IDF, lo que representa una mejora crítica para escalabilidad.
2. **Solapamiento parcial:** El solapamiento del 40-60% indica que BM25 encuentra documentos relevantes diferentes, ampliando la cobertura de resultados.
3. **Consistencia en top result:** Ambos sistemas identifican el mismo documento como más relevante, lo que valida la precisión de BM25.
4. **Diferente ranking interno:** BM25 ordena los resultados de manera diferente después del primer resultado, priorizando términos técnicos específicos.

## Decisiones de Diseño Tomadas
- **Mantener sistemas paralelos:** Se confirmó la decisión de mantener ambos sistemas funcionando en paralelo para permitir comparaciones continuas.
- **Formato de reporte unificado:** Se diseñó un formato JSON común para almacenar resultados de todos los sistemas, facilitando análisis posteriores.
- **Métricas de comparación:** Se seleccionaron métricas clave (tiempo, solapamiento, ranking) para evaluar objetivamente los sistemas.

## Próximos Pasos
- [ ] Optimizar parámetros k1 y b de BM25 para mejorar precisión
- [ ] Ejecutar pruebas con el conjunto completo de consultas de evaluación
- [ ] Implementar sistema de Sentence Transformers para comparación triple
- [ ] Crear visualizaciones de resultados comparativos
- [ ] Documentar metodología para la Fase 2

## Contribuciones al Paper Científico
**Sección del paper afectada:** Metodología y Resultados Experimentales
**Contenido agregado:** Comparación cuantitativa entre TF-IDF y BM25 para búsqueda de documentos jurídicos
**Evidencia generada:** Métricas de rendimiento, tiempos de ejecución, análisis de solapamiento

---
*Documento generado: 2025-06-05 15:15*
*Tiempo total de trabajo: 3 horas*
*Estado del proyecto: 25% completado*
