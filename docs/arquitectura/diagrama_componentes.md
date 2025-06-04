# Diagrama y Descripción de Componentes

## Diagrama de Componentes

![Diagrama de Componentes](../assets/diagrama_componentes.png)

*Nota: El diagrama de componentes es una representación visual que se puede crear posteriormente.*

## Componentes del Sistema

### 1. Procesador de PDFs (`src/text_processor/pdf_extractor.py`)

**Responsabilidad**: Extraer texto de documentos PDF.

**Componentes internos**:
- `extract_text_from_pdf`: Extrae texto de un PDF específico
- `extract_text_from_directory`: Procesa todos los PDFs en un directorio

**Dependencias**:
- PyMuPDF (fitz): Para la extracción de texto de PDFs
- Logging: Para registro de operaciones

**Entradas/Salidas**:
- **Entrada**: Archivos PDF en `data/raw/`
- **Salida**: Archivos de texto en `data/raw/` con el mismo nombre base

### 2. Preprocesador de Texto (`src/text_processor/data_preprocessor.py`)

**Responsabilidad**: Limpiar, normalizar y segmentar el texto extraído.

**Componentes internos**:
- `clean_text`: Elimina caracteres especiales, normaliza espacios
- `normalize_text`: Normaliza acentos, mayúsculas/minúsculas
- `chunk_text_by_titles`: Segmenta el texto en chunks basados en títulos
- `preprocess_raw_text`: Función principal que coordina el proceso

**Dependencias**:
- Expresiones regulares (re): Para patrones de limpieza y segmentación
- JSON: Para almacenamiento de chunks

**Entradas/Salidas**:
- **Entrada**: Texto extraído de PDFs
- **Salida**: Chunks de texto procesados en formato JSON

### 3. Procesador de Directiva Limpia (`src/ai/process_clean_directive.py`)

**Responsabilidad**: Procesar un documento específico, crear chunks y vectorstore.

**Componentes internos**:
- `DirectivaLimpiaProcessor`: Clase principal que encapsula el procesamiento
  - `verify_file_exists`: Verifica la existencia del archivo PDF
  - `extract_text_from_pdf`: Extrae texto página por página
  - `create_chunks`: Crea chunks con metadatos
  - `save_chunks_to_json`: Guarda chunks en formato JSON
  - `create_vectorstore`: Crea vectorstore con TF-IDF y NearestNeighbors
  - `save_vectorstore`: Guarda vectorstore en formato pickle
  - `process_complete_pipeline`: Ejecuta el pipeline completo

**Dependencias**:
- PyMuPDF (fitz): Para extracción de texto
- scikit-learn: Para vectorización TF-IDF y NearestNeighbors
- pickle: Para serialización del vectorstore

**Entradas/Salidas**:
- **Entrada**: PDF limpio específico
- **Salida**: Chunks JSON y vectorstore pickle

### 4. Buscador Inteligente (`src/ai/search_smart_directive.py`)

**Responsabilidad**: Realizar búsquedas inteligentes combinando métodos exactos y semánticos.

**Componentes internos**:
- `SmartDirectiveSearcher`: Clase principal para búsquedas
  - `load_vectorstore`: Carga el vectorstore desde archivo pickle
  - `exact_search`: Realiza búsqueda exacta por términos
  - `semantic_search`: Realiza búsqueda semántica con TF-IDF
  - `smart_search`: Combina resultados de búsqueda exacta y semántica
  - `display_smart_results`: Muestra resultados de forma amigable
  - `suggest_alternatives`: Sugiere búsquedas alternativas
  - `search_interactive`: Interfaz interactiva de búsqueda

**Dependencias**:
- scikit-learn: Para operaciones con vectores
- numpy: Para cálculos numéricos

**Entradas/Salidas**:
- **Entrada**: Consulta del usuario y vectorstore cargado
- **Salida**: Resultados relevantes con contexto

### 5. Configuración del Sistema (`config/settings.py`)

**Responsabilidad**: Centralizar configuraciones y rutas del sistema.

**Componentes internos**:
- Definición de rutas base
- Configuración de nombres de archivos
- Carga de variables de entorno

**Dependencias**:
- pathlib: Para manejo de rutas
- dotenv: Para carga de variables de entorno

**Entradas/Salidas**:
- **Entrada**: Variables de entorno (opcional)
- **Salida**: Configuraciones disponibles para otros módulos

## Interacciones entre Componentes

1. **Flujo de Procesamiento de Documentos**:
   ```
   PDF Extractor → Preprocesador de Texto → Procesador de Directiva → Vectorstore
   ```

2. **Flujo de Búsqueda**:
   ```
   Consulta de Usuario → Buscador Inteligente → Vectorstore → Resultados
   ```

3. **Dependencias de Configuración**:
   ```
   Configuración del Sistema → Todos los componentes
   ```

## Interfaces y Contratos

### Interfaz de Extracción de PDF
- **Entrada**: Ruta a archivo PDF o directorio
- **Salida**: Texto extraído o archivos de texto
- **Contrato**: Debe manejar errores de archivo no encontrado o PDF corrupto

### Interfaz de Preprocesamiento
- **Entrada**: Texto crudo
- **Salida**: Texto limpio y chunks
- **Contrato**: Debe preservar la estructura semántica del documento

### Interfaz de Vectorización
- **Entrada**: Chunks de texto
- **Salida**: Vectorstore con vectores TF-IDF y modelo de vecinos
- **Contrato**: Debe permitir búsquedas eficientes por similitud

### Interfaz de Búsqueda
- **Entrada**: Consulta de usuario y vectorstore
- **Salida**: Resultados relevantes ordenados
- **Contrato**: Debe combinar resultados de diferentes métodos de búsqueda

## Consideraciones de Diseño

- **Acoplamiento Bajo**: Los componentes están diseñados para funcionar de manera independiente.
- **Cohesión Alta**: Cada componente tiene una responsabilidad clara y bien definida.
- **Extensibilidad**: El diseño permite agregar nuevos métodos de procesamiento o búsqueda.
- **Mantenibilidad**: La separación de responsabilidades facilita el mantenimiento y la evolución del sistema.
