
# Contexto del Proyecto vm-expedientes-minedu

## 1. Descripción General
Este proyecto es un asistente de inteligencia artificial especializado en la normativa y disposiciones del Ministerio de Educación del Perú (MINEDU). Su objetivo principal es facilitar la búsqueda semántica e híbrida sobre documentos normativos relacionados con control previo, contabilidad y abastecimiento.

## 2. Estado Actual

### Estructura del Proyecto
El proyecto está organizado en las siguientes carpetas principales:
- `api/`: Carpeta vacía, reservada para futuros endpoints web
- `config/`: Contiene configuraciones y metadatos
- `data/`: Estructura para almacenar documentos  
  - `categories/`: Carpeta vacía para categorización futura  
  - `processed/`: Contiene archivos generados (chunks, vectorstores, JSONs)  
  - `raw/`: Carpeta vacía para almacenar PDFs originales
- `docs/`: Carpeta vacía para documentación futura
- `src/`: Código fuente principal  
  - `ai/`: Scripts de IA y vectorstores  
  - `pdf_processor/`: Procesamiento de PDFs  
  - `text_processor/`: Limpieza y procesamiento de texto
- `tests/`: Pruebas unitarias del sistema

### Componentes Principales Implementados
1. **Generación de Vectorstore**  
   - Ubicación: `src/ai/generate_vectorstore_full_v2.py`  
   - Funcionalidad: Crea un vectorstore robusto con metadatos usando TF-IDF y NearestNeighbors  
   - Salida: `data/processed/vectorstore_semantic_full_v2.pkl`

2. **Búsqueda Híbrida**  
   - Ubicación: `src/ai/search_vectorstore_hybrid.py`  
   - Funcionalidad: Realiza búsquedas combinando dos métodos:  
     - TF-IDF + cosine similarity  
     - Embedding + NearestNeighbors

3. **Preprocesamiento**  
   - Limpieza de texto: `src/text_processor/text_cleaner_v2.py`  
   - Chunking: `src/text_processor/text_chunker_v2.py`  
   - Exportación: `src/text_processor/chunks_to_json.py`

4. **Herramientas de Debugging**  
   - `src/ai/inspect_vectorstore.py`: Para inspeccionar el contenido del vectorstore  
   - `test_script.py`: Script básico de prueba

## 3. Entorno de Desarrollo
- Python 3.11.11  
- Entorno virtual: minedu-env (Miniconda)  
- Terminal: PowerShell  
- Ruta ejecutable: `C:\Users\hanns\miniconda3\envs\minedu-env\python.exe`

## 4. Comandos Principales
```bash
# Generar vectorstore
python src/ai/generate_vectorstore_full_v2.py

# Realizar búsqueda
python src/ai/search_vectorstore_hybrid.py

# Inspeccionar vectorstore
python src/ai/inspect_vectorstore.py
