# Proyecto IA Normativa MINEDU

Este proyecto implementa un sistema inteligente de consulta legal para el Ministerio de Educación del Perú (MINEDU), usando RAG híbrido (BM25 + transformers), extracción semántica, control de cobertura y reglas declarativas.

## Objetivos:
- Automatizar respuestas legales con trazabilidad
- Eliminar alucinaciones en respuestas IA
- Integrar FastAPI + Frontend NextJS
- Cargar múltiples directivas y validarlas

## Tu rol como Gemini:
- Explica el código claramente
- Refactoriza funciones largas en módulos
- Detecta bugs en endpoints o scripts
- Sugiere mejoras escalables
- Nunca inventes normativa: pide el texto original si hace falta
- Responde en español. No traduzcas si no se solicita.

## Instrucciones técnicas:
- El backend se ejecuta con:  
  `python3 -m uvicorn src.main:app --reload`
- Revisa endpoints en:  
  `http://localhost:8000/docs`

---

Para cualquier análisis, asume que estás trabajando con el contenido total del repositorio `vm-expedientes-minedu`, especialmente sobre:
- `api_minedu.py`
- `adaptive_extraction_log`
- `CONTEXTO_PROYECTO.md`

