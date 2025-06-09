# Informe de Evaluación del Pipeline RAG MINEDU

Fecha: 2025-06-06 04:06:43

## Resumen General

| Métrica | Valor |
|---------|-------|
| avg_length_ratio | 1.5161 |
| avg_exact_match | 0.0000 |
| avg_token_overlap | 0.4175 |
| avg_query_time | 0.9955 |
| total_questions | 20.0000 |
| total_time | 19.9232 |
| avg_time_per_question | 0.9962 |

## Estadísticas Descriptivas

|       |   query_time |   exact_match |   token_overlap |   length_ratio |
|:------|-------------:|--------------:|----------------:|---------------:|
| count |    20        |            20 |       20        |      20        |
| mean  |     0.995538 |             0 |        0.417524 |       1.51607  |
| std   |     0.288485 |             0 |        0.329695 |       0.62149  |
| min   |     0.504092 |             0 |        0        |       0.859259 |
| 25%   |     0.727322 |             0 |        0.170814 |       1.10826  |
| 50%   |     1.05657  |             0 |        0.233032 |       1.36362  |
| 75%   |     1.21647  |             0 |        0.75     |       1.59381  |
| max   |     1.4602   |             0 |        1        |       3.06667  |
## Análisis por Pregunta

### Mejores Preguntas (por solapamiento de tokens)

| query_id   | question                                                          |   token_overlap |
|:-----------|:------------------------------------------------------------------|----------------:|
| Q006       | ¿Cuál es el monto máximo para viáticos internacionales en Europa? |        1        |
| Q003       | ¿Qué documentos se requieren para solicitar viáticos?             |        0.888889 |
| Q007       | ¿Qué gastos no son reembolsables en una comisión de servicios?    |        0.846154 |
### Peores Preguntas (por solapamiento de tokens)

| query_id   | question                                                                      |   token_overlap |
|:-----------|:------------------------------------------------------------------------------|----------------:|
| Q018       | ¿Qué norma regula el procedimiento administrativo disciplinario en el MINEDU? |        0        |
| Q012       | ¿Qué requisitos debe cumplir una declaración jurada de gastos?                |        0.05     |
| Q017       | ¿Cuál es el monto máximo para caja chica por dependencia?                     |        0.111111 |
## Conclusiones

- Este informe presenta un análisis automático de los resultados de evaluación.
- Se recomienda revisar los gráficos generados para un análisis visual más detallado.
- Las métricas principales a considerar son: token_overlap, faithfulness (si está disponible) y tiempo de consulta.
