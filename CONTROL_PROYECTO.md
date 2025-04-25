ESCANEO GENERAL DEL PROYECTO: vm-expedientes-minedu

Este documento resume de forma completa y ordenada el contenido, estructura y estado actual del proyecto. Puedes entregárselo a cualquier LLM para que entienda tu flujo de trabajo, organización y archivos clave sin necesidad de más contexto.

✨ OBJETIVO GENERAL

Desarrollar un asistente inteligente que permita realizar búsquedas semánticas e híbridas sobre normativas del Ministerio de Educación del Perú, utilizando procesamiento de texto y embeddings generados localmente con TF-IDF.

📂 ESTRUCTURA PRINCIPAL DE CARPETAS

vm-expedientes-minedu/
├── api/                        # [Vacío o futuro desarrollo de endpoints]
├── config/                     # Configuraciones o metadatos auxiliares
├── data/
│   ├── categories/             # [Vacío]
│   ├── processed/              # Archivos generados (chunks, vectorstores, JSONs)
│   ├── raw/                    # [Vacío]
├── docs/                       # [Vacío, reservado para documentación]
├── src/
│   ├── ai/                     # Scripts principales de IA y vectorstores
│   ├── pdf_processor/          # [Vacío o en desarrollo]
│   ├── text_processor/         # Limpieza, chunking, conversiones
├── tests/                      # Unit tests del sistema (PyMuPDF, semantic search)
├── .env                        # Variables de entorno
├── CONTROL_PROYECTO.md        # Checklist del progreso del proyecto
├── README.md                  # Introducción general
├── requirements.txt           # Dependencias para reproducir el entorno

📃 ARCHIVOS CLAVE Y SU FUNCIÓN

1. Generación de Vectorstore

src/ai/generate_vectorstore_full_v2.py: genera el vectorstore robusto con metadatos. Usa:

chunks_v2.json (mejorados)

TF-IDF y NearestNeighbors (cosine)

Guarda en: data/processed/vectorstore_semantic_full_v2.pkl

2. Búsqueda Híbrida

src/ai/search_vectorstore_hybrid.py: realiza una consulta con doble método:

TF-IDF + cosine

Embedding + NearestNeighbors

Compara ambos resultados y reporta coincidencias

3. Preprocesamiento

src/text_processor/text_cleaner_v2.py: [limpieza de texto, actualizado]

src/text_processor/text_chunker_v2.py: [divide los documentos en chunks con metadatos]

src/text_processor/chunks_to_json.py: exporta los chunks a chunks_v2.json

4. Inspección / debugging

src/ai/inspect_vectorstore.py: imprime las claves contenidas en el vectorstore .pkl

test_script.py: script de prueba de ejecución básico ("Hello World")

💡 ESTADO ACTUAL DEL PROYECTO



🛠️ ENTORNO Y CONFIGURACIÓN

Python 3.11.11

Entorno virtual con Miniconda: minedu-env

Ejecutable: C:\Users\hanns\miniconda3\envs\minedu-env\python.exe

Terminal de uso: PowerShell (con soporte para rutas absolutas y relativas)

🔗 INSTRUCCIONES RÁPIDAS PARA OTROS LLMS

1. Generar vectorstore:

python src/ai/generate_vectorstore_full_v2.py

2. Buscar por consulta:

python src/ai/search_vectorstore_hybrid.py

3. Testear vectorstore:

python src/ai/inspect_vectorstore.py

🌌 PRÓXIMOS PASOS

Agregar mejoras a la respuesta semántica para que entregue valores clave (como montos, fechas)

Integrar interfaz CLI/web (fase futura)

Escalar a otros documentos PDF para permitir respuestas cruzadas entre normas

Exportar datos en formatos estructurados (JSON, Excel, etc)

Actualizado: 24 de abril de 2025Autor: Hanns (usuario) con apoyo de LLM (modo escaneo inteligente)