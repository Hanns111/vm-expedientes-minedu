# Arquitectura del Sistema

## Pipeline Completo
PDF → OCR Cleaning → Chunking → Multiple Vectorization → Hybrid Search → Entity Extraction

## Componentes Implementados

### FASE 1 - BM25 (COMPLETADO)
- **Componentes principales:**
  - `generate_vectorstore_bm25.py`: Generación de índice BM25 optimizado para documentos normativos
  - `search_vectorstore_bm25.py`: Sistema de búsqueda con filtros de calidad y extracción de entidades
  - `compare_tfidf_bm25.py`: Herramienta de comparación científica entre sistemas
- **Mejoras implementadas:**
  - Normalización de acentos y caracteres especiales
  - Tokenización optimizada para español jurídico
  - Filtros de calidad para resultados
  - 55-68% mejora en velocidad vs TF-IDF

### FASE 2 - Sentence Transformers (EN PROGRESO)
- **Modelo seleccionado:** paraphrase-multilingual-MiniLM-L12-v2
- **Justificación:** Soporte nativo para español, tamaño compacto, buen rendimiento en tareas de similitud semántica
- **Objetivo:** Comprensión semántica mejorada para consultas en lenguaje natural
- **Componentes planificados:**
  - `generate_vectorstore_transformer.py`: Generación de embeddings y vectorstore
  - `search_vectorstore_transformer.py`: Búsqueda semántica con reranking
  - `compare_transformer_bm25.py`: Comparación científica con sistemas léxicos

### FASE 3 - FAISS (PLANIFICADO)
- **Objetivo:** Optimización de velocidad para búsqueda a gran escala
- **Componentes planificados:**
  - Indexación FAISS para embeddings de transformers
  - Búsqueda aproximada de vecinos más cercanos
  - Evaluación de compromiso precisión-velocidad

### FASE 4 - Sistema Híbrido (PLANIFICADO)
- **Objetivo:** Combinar fortalezas de sistemas léxicos y semánticos
- **Componentes planificados:**
  - Sistema de ponderación adaptativa
  - Reranking inteligente de resultados
  - Extracción avanzada de entidades y contexto

## Diagrama de Arquitectura

```
┌───────────┐     ┌───────────┐     ┌───────────┐     ┌───────────┐
│           │     │           │     │           │     │           │
│  PDF Raw  │────▶│  OCR &    │────▶│  Text     │────▶│  Chunks   │
│           │     │  Cleaning │     │  Chunking │     │  JSON     │
└───────────┘     └───────────┘     └───────────┘     └───────────┘
                                                           │
                                                           ▼
┌───────────┐     ┌───────────┐     ┌───────────┐     ┌───────────┐
│           │     │           │     │           │     │           │
│  Hybrid   │◀────│ Semantic  │◀────│   BM25    │◀────│ Multiple  │
│  Search   │     │ Vectorstore│     │ Vectorstore│    │Vectorization│
└───────────┘     └───────────┘     └───────────┘     └───────────┘
      │
      ▼
┌───────────┐     ┌───────────┐
│           │     │           │
│  Entity   │────▶│  Response │
│ Extraction│     │ Generation│
└───────────┘     └───────────┘
```

## Tecnologías Utilizadas

- **Procesamiento de PDF:** PyMuPDF (fitz)
- **Procesamiento de texto:** Regex, NLTK, Spacy
- **Vectorización léxica:** Scikit-learn TF-IDF, rank_bm25
- **Vectorización semántica:** Sentence-Transformers, HuggingFace
- **Optimización de búsqueda:** FAISS
- **Evaluación científica:** Métricas de IR (Precision, Recall, F1)

## Consideraciones de Diseño

- **Robustez:** Manejo de errores OCR y texto corrupto
- **Escalabilidad:** Arquitectura para soportar 300K+ documentos
- **Rendimiento:** Optimización para consultas en tiempo real (<1s)
- **Precisión:** Enfoque en relevancia de resultados para contexto normativo
- **Mantenibilidad:** Código modular y bien documentado
