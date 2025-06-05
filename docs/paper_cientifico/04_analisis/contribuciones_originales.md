# Contribuciones Originales del Proyecto

## Innovaciones Técnicas

### 1. Preprocesamiento Robusto para Documentos Normativos
- **Problema abordado:** Los documentos normativos gubernamentales frecuentemente contienen errores de OCR, formatos inconsistentes y estructuras complejas que dificultan su procesamiento automático.
- **Contribución:** Desarrollo de un pipeline de preprocesamiento especializado para documentos normativos que incluye:
  - Corrección de errores comunes de OCR en documentos legales en español
  - Normalización de formatos específicos de normativas (numeraciones, referencias cruzadas)
  - Preservación de la estructura jerárquica de los documentos normativos
- **Impacto:** Mejora significativa en la calidad del texto procesado, reduciendo errores en etapas posteriores del sistema.

### 2. Chunking Optimizado para Contexto Normativo
- **Problema abordado:** Los métodos tradicionales de chunking (división por caracteres o párrafos) no preservan adecuadamente el contexto en documentos normativos.
- **Contribución:** Algoritmo de chunking basado en patrones normativos que:
  - Identifica y preserva secciones completas según numeración legal
  - Mantiene referencias contextuales entre secciones relacionadas
  - Optimiza el tamaño de chunks para equilibrar contexto y precisión
- **Impacto:** Chunks más coherentes y autocontenidos, mejorando la relevancia de resultados de búsqueda.

### 3. Sistema Híbrido Adaptativo
- **Problema abordado:** Los sistemas puramente léxicos (BM25) o puramente semánticos (Transformers) tienen limitaciones específicas para consultas normativas.
- **Contribución:** Diseño de un sistema híbrido que:
  - Combina búsqueda léxica rápida con comprensión semántica profunda
  - Implementa ponderación adaptativa según tipo de consulta
  - Optimiza el rendimiento para consultas en español sobre normativa técnica
- **Impacto:** Sistema que aprovecha lo mejor de ambos enfoques, ofreciendo velocidad y precisión semántica.

## Contribuciones Metodológicas

### 1. Protocolo de Evaluación para Sistemas de Búsqueda Normativos
- **Problema abordado:** Falta de estándares específicos para evaluar sistemas de búsqueda en documentos normativos gubernamentales.
- **Contribución:** Desarrollo de un protocolo de evaluación que:
  - Define métricas específicas para el contexto normativo
  - Establece consultas estándar representativas de casos reales
  - Combina evaluación cuantitativa y cualitativa
- **Impacto:** Marco metodológico replicable para evaluación de sistemas similares.

### 2. Análisis Comparativo Riguroso
- **Problema abordado:** Escasez de estudios comparativos detallados entre enfoques léxicos y semánticos para documentos en español.
- **Contribución:** Análisis científico que:
  - Compara sistemáticamente rendimiento de diferentes técnicas
  - Documenta compromisos entre velocidad y precisión
  - Identifica casos específicos donde cada enfoque destaca
- **Impacto:** Evidencia empírica para informar decisiones de diseño en sistemas similares.

## Contribuciones Prácticas

### 1. Implementación en Entorno Gubernamental Real
- **Problema abordado:** Brecha entre investigación académica y aplicación práctica en entidades gubernamentales.
- **Contribución:** Despliegue de un sistema funcional que:
  - Se integra con procesos administrativos existentes
  - Demuestra viabilidad en entorno con recursos limitados
  - Documenta desafíos y soluciones de implementación
- **Impacto:** Caso de estudio replicable para otras entidades gubernamentales.

### 2. Código Abierto y Documentación Científica
- **Problema abordado:** Falta de recursos abiertos para sistemas de IA aplicados a documentos normativos en español.
- **Contribución:** Publicación de:
  - Código fuente completo y bien documentado
  - Protocolos de evaluación detallados
  - Documentación científica rigurosa
- **Impacto:** Recursos valiosos para investigadores y desarrolladores trabajando en problemas similares.

## Limitaciones Reconocidas

1. **Escala de datos:** El sistema actual se ha probado con un conjunto limitado de documentos. Se requieren pruebas con corpus más grandes para validar la escalabilidad.

2. **Especificidad del dominio:** Las optimizaciones están enfocadas en documentos normativos del MINEDU Perú. La generalización a otros dominios o países requeriría adaptaciones.

3. **Evaluación de usuario final:** Si bien se han realizado evaluaciones técnicas exhaustivas, se necesitan más pruebas con usuarios finales para validar la utilidad práctica.

## Trabajo Futuro

1. **Expansión del corpus:** Incorporar más documentos normativos para probar la escalabilidad.

2. **Mejoras en extracción de entidades:** Desarrollar capacidades avanzadas para identificar automáticamente entidades normativas específicas.

3. **Interfaz conversacional:** Evolucionar hacia un asistente conversacional que pueda mantener contexto entre consultas relacionadas.

4. **Evaluación longitudinal:** Realizar seguimiento a largo plazo del uso del sistema en entorno real para medir impacto.
