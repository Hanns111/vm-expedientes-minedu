# Flujo de Datos en el Sistema

Este documento describe en detalle el flujo de datos a través del sistema Asistente IA MINEDU, desde la ingesta de documentos PDF hasta la presentación de resultados de búsqueda al usuario.

## Diagrama de Flujo de Datos

![Diagrama de Flujo de Datos](../assets/diagrama_flujo_datos.png)

*Nota: El diagrama de flujo de datos es una representación visual que se puede crear posteriormente.*

## Etapas del Flujo de Datos

### 1. Ingesta de Documentos

**Descripción**: Proceso de incorporación de documentos PDF al sistema.

**Flujo detallado**:
1. El usuario coloca documentos PDF en el directorio `data/raw/`
2. El sistema identifica los nuevos documentos PDF
3. Se registra la metadata básica del documento (nombre, tamaño, fecha)

**Formatos de datos**:
- **Entrada**: Archivos PDF (`.pdf`)
- **Salida**: Registro de documentos disponibles

### 2. Extracción de Texto

**Descripción**: Proceso de extracción del contenido textual de los documentos PDF.

**Flujo detallado**:
1. El sistema lee el documento PDF página por página
2. Se extrae el texto de cada página usando PyMuPDF
3. Se concatena el texto extraído con marcadores de página
4. Se guarda el texto extraído en un archivo de texto plano

**Formatos de datos**:
- **Entrada**: Archivo PDF
- **Salida**: Archivo de texto (`.txt`) con marcadores de página

**Transformaciones**:
- Conversión de contenido PDF a texto plano
- Inserción de marcadores de página (`--- PÁGINA X ---`)

### 3. Preprocesamiento de Texto

**Descripción**: Limpieza, normalización y preparación del texto para su procesamiento.

**Flujo detallado**:
1. Se lee el archivo de texto extraído
2. Se aplican operaciones de limpieza:
   - Eliminación de caracteres especiales no deseados
   - Normalización de espacios y saltos de línea
   - Corrección de palabras cortadas entre líneas
3. Se normaliza el texto:
   - Conversión a minúsculas (cuando corresponde)
   - Normalización de acentos
   - Estandarización de formatos numéricos y fechas

**Formatos de datos**:
- **Entrada**: Texto crudo con posibles errores de formato
- **Salida**: Texto limpio y normalizado

**Transformaciones**:
- Aplicación de expresiones regulares para limpieza
- Normalización de caracteres y formatos

### 4. Segmentación en Chunks

**Descripción**: División del texto en segmentos manejables con metadatos.

**Flujo detallado**:
1. Se analiza el texto para identificar límites naturales (títulos, secciones)
2. Se segmenta el texto en chunks de tamaño apropiado (aproximadamente 1000 palabras)
3. Se generan metadatos para cada chunk:
   - ID único
   - Conteo de palabras y caracteres
   - Números de página
   - Índice del chunk
   - Archivo fuente
   - Fecha de creación

**Formatos de datos**:
- **Entrada**: Texto limpio y normalizado
- **Salida**: Lista de chunks con metadatos en formato JSON

**Transformaciones**:
- Segmentación basada en patrones de títulos y tamaño máximo
- Generación de metadatos para cada chunk

### 5. Vectorización

**Descripción**: Conversión de chunks de texto a representaciones vectoriales para búsqueda semántica.

**Flujo detallado**:
1. Se preparan los chunks para vectorización
2. Se aplica TF-IDF Vectorizer para convertir texto a vectores:
   - Configuración de 5000 características máximas
   - Uso de n-gramas (1,2)
   - Filtrado de términos muy comunes o muy raros
3. Se crea un modelo de vecinos más cercanos (NearestNeighbors) con los vectores
4. Se construye el vectorstore con:
   - Vectorizador entrenado
   - Matriz TF-IDF
   - Modelo de vecinos más cercanos
   - Chunks originales
   - Metadatos del proceso

**Formatos de datos**:
- **Entrada**: Chunks de texto con metadatos
- **Salida**: Vectorstore serializado (`.pkl`) con vectores y modelo

**Transformaciones**:
- Conversión de texto a vectores numéricos mediante TF-IDF
- Creación de índice de similitud para búsqueda eficiente

### 6. Consulta del Usuario

**Descripción**: Recepción y procesamiento de la consulta del usuario.

**Flujo detallado**:
1. El usuario ingresa una consulta de texto
2. Se limpia y normaliza la consulta
3. Se prepara la consulta para búsqueda exacta y semántica

**Formatos de datos**:
- **Entrada**: Texto de consulta del usuario
- **Salida**: Consulta procesada

**Transformaciones**:
- Limpieza básica de la consulta
- Normalización para compatibilidad con el índice

### 7. Búsqueda Híbrida

**Descripción**: Proceso de búsqueda que combina métodos exactos y semánticos.

**Flujo detallado**:
1. **Búsqueda Exacta**:
   - Se buscan coincidencias exactas de la consulta en los chunks
   - Se calcula relevancia basada en frecuencia y posición
   - Se extrae contexto alrededor de las coincidencias
2. **Búsqueda Semántica**:
   - Se vectoriza la consulta usando el mismo vectorizador
   - Se buscan vecinos más cercanos en el espacio vectorial
   - Se calculan puntuaciones de similitud
3. **Combinación de Resultados**:
   - Se fusionan resultados de ambos métodos
   - Se aplica ponderación para balancear métodos
   - Se eliminan duplicados y se ordenan por relevancia

**Formatos de datos**:
- **Entrada**: Consulta procesada y vectorstore
- **Salida**: Lista ordenada de resultados relevantes

**Transformaciones**:
- Conversión de consulta a vector
- Cálculo de similitudes y relevancia
- Fusión y ordenamiento de resultados

### 8. Presentación de Resultados

**Descripción**: Formateo y presentación de resultados al usuario.

**Flujo detallado**:
1. Se toman los resultados ordenados por relevancia
2. Se formatea cada resultado para mostrar:
   - Contexto relevante con la consulta
   - Metadatos (páginas, tipo de coincidencia)
   - Puntuación de relevancia
3. Se ofrecen opciones para ver resultados completos
4. Se sugieren búsquedas alternativas relacionadas

**Formatos de datos**:
- **Entrada**: Lista de resultados relevantes
- **Salida**: Presentación formateada para el usuario

**Transformaciones**:
- Extracción de contexto relevante
- Formateo para presentación legible

## Almacenamiento de Datos

### Archivos de Datos Intermedios

1. **Texto Extraído** (`data/raw/[nombre_documento].txt`):
   - Texto crudo extraído del PDF
   - Incluye marcadores de página

2. **Texto Limpio** (`data/processed/texto_limpio.txt`):
   - Texto después de limpieza y normalización
   - Formato de texto plano

3. **Chunks JSON** (`data/processed/chunks_directiva_limpia.json`):
   - Lista de chunks con metadatos
   - Formato JSON estructurado

4. **Vectorstore** (`data/processed/vectorstore_directiva_limpia.pkl`):
   - Vectorizador TF-IDF entrenado
   - Matriz TF-IDF de chunks
   - Modelo NearestNeighbors
   - Chunks originales
   - Metadatos del proceso
   - Formato pickle serializado

## Consideraciones de Rendimiento y Escalabilidad

- **Tamaño de Chunks**: El tamaño de los chunks (aproximadamente 1000 palabras) está optimizado para equilibrar contexto y precisión en la búsqueda.
- **Dimensionalidad de Vectores**: La configuración de 5000 características máximas en TF-IDF equilibra riqueza semántica y eficiencia.
- **Almacenamiento**: El uso de pickle para el vectorstore permite una carga rápida pero puede presentar limitaciones de escalabilidad con muchos documentos.
- **Procesamiento por Lotes**: El sistema actual procesa documentos individualmente, pero podría adaptarse para procesamiento por lotes.

## Puntos de Mejora en el Flujo de Datos

1. **Paralelización**: Implementar procesamiento paralelo para la extracción y vectorización de múltiples documentos.
2. **Indexación Incremental**: Permitir actualización incremental del vectorstore sin reprocesar todos los documentos.
3. **Compresión de Vectores**: Implementar técnicas de compresión para reducir el tamaño del vectorstore.
4. **Caché de Resultados**: Implementar caché para consultas frecuentes y mejorar tiempo de respuesta.
5. **Retroalimentación**: Incorporar mecanismos de retroalimentación del usuario para mejorar resultados futuros.
