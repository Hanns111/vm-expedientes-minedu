# Checklist Diario de Desarrollo

## Documentación Científica
- [ ] Actualizar diario de desarrollo con fecha actual (`docs/paper_cientifico/05_diario_desarrollo/YYYY-MM-DD_tema.md`)
- [ ] Registrar decisiones técnicas tomadas y su justificación
- [ ] Documentar problemas encontrados y soluciones implementadas
- [ ] Actualizar métricas de rendimiento si se realizaron pruebas
- [ ] Revisar y actualizar la documentación de arquitectura si hubo cambios

## Control de Código
- [ ] Ejecutar tests unitarios antes de commit
- [ ] Verificar que no haya archivos corruptos o innecesarios
- [ ] Seguir convención de commits: `[FASE-X][COMPONENTE] Descripción concisa`
- [ ] Actualizar CHANGELOG.md si hay cambios significativos
- [ ] Verificar que no se incluyan credenciales o datos sensibles

## Gestión de Datos
- [ ] Verificar integridad de archivos de datos utilizados
- [ ] Confirmar que los PDFs fuente son los correctos (DIRECTIVA N° 011-2020-MINEDU_LIMPIA.pdf)
- [ ] Respaldar vectorstores generados si hubo modificaciones
- [ ] Documentar cualquier cambio en la estructura de datos

## Experimentos y Resultados
- [ ] Registrar parámetros exactos utilizados en experimentos
- [ ] Guardar resultados de comparaciones en formato estándar
- [ ] Incluir capturas de pantalla o ejemplos relevantes
- [ ] Analizar y documentar patrones observados en los resultados

## Planificación
- [ ] Actualizar estado de tareas en curso
- [ ] Identificar bloqueantes o dependencias
- [ ] Planificar próximos pasos con detalle
- [ ] Revisar cronograma de la fase actual

## Convenciones de Commits

### Formato
```
[FASE-X][COMPONENTE] Descripción concisa

Descripción detallada de los cambios realizados.
- Punto 1
- Punto 2

Issue: #XX (si aplica)
```

### Componentes
- `DOCS`: Documentación
- `PDF`: Procesamiento de PDFs
- `TEXT`: Procesamiento de texto
- `TFIDF`: Vectorstore TF-IDF
- `BM25`: Vectorstore BM25
- `TRANS`: Transformers
- `FAISS`: Optimización FAISS
- `HYBRID`: Sistema híbrido
- `TEST`: Pruebas y evaluación
- `INFRA`: Infraestructura y configuración

### Ejemplos
```
[FASE-1][BM25] Optimizar tokenización para consultas

- Implementada normalización de acentos
- Mejorado manejo de caracteres especiales
- Agregados tests de validación

Issue: #12
```

```
[FASE-2][DOCS] Actualizar documentación de arquitectura

- Agregado diagrama de flujo para Sentence Transformers
- Documentadas decisiones de diseño para embeddings
- Actualizada lista de dependencias
```

## Etiquetas de Versión

### Formato
`vX.Y.Z-faseN`

- `X`: Cambio mayor (breaking change)
- `Y`: Nueva funcionalidad
- `Z`: Corrección de bugs
- `faseN`: Fase del proyecto (fase1, fase2, etc.)

### Ejemplos
- `v0.1.0-fase1`: Primera versión funcional de la Fase 1
- `v0.1.1-fase1`: Corrección de bugs en Fase 1
- `v0.2.0-fase2`: Primera versión de Fase 2
- `v1.0.0-prod`: Versión de producción
