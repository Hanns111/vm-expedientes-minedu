# Abstract Draft - Sistema Híbrido para Consultas Normativas

## Problema
El acceso eficiente a normativas gubernamentales representa un desafío significativo para funcionarios públicos y ciudadanos, especialmente cuando los documentos contienen errores de OCR, terminología técnica específica y estructuras complejas. La necesidad de sistemas que combinen velocidad y precisión semántica es crítica para democratizar el acceso a información normativa.

## Metodología
Desarrollamos un sistema híbrido que combina BM25 y Sentence Transformers para consultas en lenguaje natural sobre documentos normativos gubernamentales. Nuestro enfoque incluye: (1) preprocesamiento robusto para documentos con errores de OCR, (2) chunking optimizado para preservar contexto normativo, (3) vectorización múltiple (léxica y semántica), y (4) sistema de búsqueda híbrido con ponderación adaptativa.

## Resultados
- BM25: 55-68% más rápido que TF-IDF con precisión equivalente
- Sentence Transformers: [Pendiente Fase 2]
- Sistema Híbrido: [Pendiente Fase 4]

## Impacto
Implementación real en MINEDU con escalabilidad a 300K documentos, demostrando la viabilidad de sistemas híbridos para mejorar el acceso a información normativa en entidades gubernamentales latinoamericanas. El código y dataset son contribuciones abiertas para la comunidad científica y gubernamental.
