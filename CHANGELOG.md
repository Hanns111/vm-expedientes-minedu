# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0-fase1] - 2025-06-05

### Añadido
- Implementación completa del sistema BM25 con preprocesamiento optimizado
- Comparación científica entre TF-IDF y BM25
- Documentación científica inicial (arquitectura, protocolos, resultados)
- Checklist diario y convenciones de control de versiones

### Cambiado
- Reemplazado PDF corrupto por versión limpia (DIRECTIVA N° 011-2020-MINEDU_LIMPIA.pdf)
- Mejorado preprocesamiento de texto para normalizar acentos y caracteres especiales
- Optimizada tokenización para consultas en español

### Corregido
- Solucionado UnicodeEncodeError en scripts de procesamiento
- Corregido problema de BM25 que no devolvía resultados
- Eliminados archivos corruptos y datos generados con fuentes incorrectas

### Eliminado
- PDF corrupto (Directiva_Viatcos_011_2020.pdf)
- Vectorstores generados con datos corruptos

## [0.0.1] - 2025-05-15

### Añadido
- Implementación inicial de extracción de texto de PDFs
- Sistema básico de chunking basado en secciones numeradas
- Vectorstore TF-IDF para búsqueda básica
- Estructura inicial del proyecto
