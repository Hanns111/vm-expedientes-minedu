# Asistente IA MINEDU - Sistema Híbrido de Consultas Normativas

Asistente de inteligencia artificial para el Ministerio de Educación del Perú, especializado en normativa y disposiciones relacionadas al control previo, contabilidad y abastecimiento.

## Estructura del Proyecto

```
├── docs/                    # Documentación del proyecto
├── data/                    # Datos y documentos procesados
│   ├── raw/                # Documentos PDF originales
│   ├── processed/          # Documentos convertidos a texto
│   └── categories/         # Documentos organizados por categorías
├── src/                    # Código fuente
│   ├── pdf_processor/      # Scripts para procesar PDFs
│   ├── text_processor/     # Scripts para procesar texto
│   └── ai/                 # Modelos y lógica de IA
├── tests/                  # Pruebas unitarias y de integración
├── config/                 # Archivos de configuración
└── api/                    # API para la interfaz web (futuro)
```

## Requisitos

- Python 3.8+
- Dependencias listadas en `requirements.txt`

## Instalación

1. Clonar el repositorio
2. Crear un entorno virtual: `python -m venv venv`
3. Activar el entorno virtual
4. Instalar dependencias: `pip install -r requirements.txt`

## Estado Actual del Proyecto
- ✅ **FASE 1 COMPLETADA:** BM25 vs TF-IDF (55-68% mejora velocidad)
- 🔄 **FASE 2 EN PROGRESO:** Sentence Transformers (comprensión semántica)
- ⏳ **FASE 3 PLANIFICADA:** FAISS (optimización velocidad)
- ⏳ **FASE 4 PLANIFICADA:** Sistema Híbrido Final

## IMPORTANTE: Fuentes de Datos
- **PDF Principal:** DIRECTIVA N° 011-2020-MINEDU_LIMPIA.pdf
- **Motivo:** Versión con OCR corregido y texto coherente
- **Evitar:** Otros PDFs pueden contener errores de OCR que corrompen resultados

## Arquitectura Implementada
PDF → OCR Cleaning → Chunking → Multiple Vectorization → Hybrid Search → Entity Extraction

## Resultados Científicos
- **Paper en preparación:** Para SIGIR/CLEF 2025-2026
- **Implementación real:** MINEDU Perú
- **Código open source:** Disponible para reproducción

## Documentación Científica
Ver `docs/paper_cientifico/` para documentación completa:
- Metodología experimental
- Resultados por fase
- Diario de desarrollo diario
- Análisis de contribuciones

## Uso

```bash
# Extracción de texto desde PDF
python src/text_processor/pdf_extractor.py --input "data/raw/DIRECTIVA N° 011-2020-MINEDU_LIMPIA.pdf" --output "data/processed/texto_limpio.txt"

# Generación de chunks
python src/text_processor/text_chunker_v2.py

# Generación de vectorstore TF-IDF
python src/ai/generate_vectorstore_full_v2.py

# Generación de vectorstore BM25
python src/ai/generate_vectorstore_bm25.py

# Comparación de sistemas de búsqueda
python src/ai/compare_tfidf_bm25.py --query "[¿Cuál es el procedimiento para solicitar viáticos?]"
```

## Contribución

Seguir el protocolo de documentación diaria en `tools/daily_checklist.md` y las convenciones de commits establecidas.

## Licencia

[Información de licencia pendiente]
