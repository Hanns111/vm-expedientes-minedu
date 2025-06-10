# Arquitectura del Asistente IA MINEDU

## Visión General

El Asistente IA MINEDU es un sistema de búsqueda semántica diseñado para facilitar el acceso y consulta de normativas del Ministerio de Educación del Perú. El sistema procesa documentos PDF, extrae su contenido, lo procesa y vectoriza para permitir búsquedas inteligentes que combinan métodos exactos y semánticos.

## Componentes Principales

![Diagrama de Arquitectura](../assets/diagrama_arquitectura.png)

*Nota: El diagrama de arquitectura es una representación visual que se puede crear posteriormente.*

La arquitectura del sistema se compone de los siguientes módulos principales:

1. **Módulo de Procesamiento de Documentos**
   - Extracción de texto de PDFs
   - Limpieza y normalización de texto
   - Segmentación en chunks con metadatos

2. **Módulo de Vectorización**
   - Creación de vectores TF-IDF
   - Almacenamiento de vectores y metadatos
   - Modelo de vecinos más cercanos (NearestNeighbors)

3. **Módulo de Búsqueda Inteligente**
   - Búsqueda exacta por coincidencia de términos
   - Búsqueda semántica por similitud de vectores
   - Combinación de resultados con ponderación

4. **Interfaz de Usuario**
   - Interfaz de línea de comandos (CLI)
   - Visualización de resultados
   - Sugerencias de búsqueda

## Flujo de Datos

El sistema sigue el siguiente flujo de datos:

1. **Entrada**: Documentos PDF de normativas del MINEDU
2. **Procesamiento**: 
   - Extracción de texto página por página
   - Limpieza y normalización del texto
   - Segmentación en chunks con metadatos (páginas, conteo de palabras)
3. **Indexación**:
   - Vectorización de chunks usando TF-IDF
   - Creación de índice de vecinos más cercanos
   - Almacenamiento de vectores y metadatos
4. **Búsqueda**:
   - Recepción de consulta del usuario
   - Procesamiento de la consulta
   - Búsqueda exacta y semántica en paralelo
   - Combinación y ranking de resultados
5. **Salida**:
   - Presentación de resultados relevantes
   - Contexto de las coincidencias
   - Opciones para ver resultados completos

## Tecnologías Utilizadas

- **Lenguaje de Programación**: Python 3.11.11
- **Extracción de PDF**: PyMuPDF (fitz)
- **Procesamiento de Texto**: Expresiones regulares, funciones de normalización
- **Vectorización**: scikit-learn (TfidfVectorizer)
- **Búsqueda Semántica**: scikit-learn (NearestNeighbors)
- **Almacenamiento**: JSON (chunks), Pickle (vectorstore)
- **Entorno**: Miniconda en Windows PowerShell

## Estructura de Directorios

```
vm-expedientes-minedu/
├── data/                    # Datos y documentos
│   ├── raw/                # Documentos PDF originales
│   └── processed/          # Chunks y vectorstores
├── src/                    # Código fuente
│   ├── text_processor/     # Procesamiento de texto y PDFs
│   └── ai/                 # Modelos y búsqueda inteligente
├── config/                 # Configuraciones del sistema
└── docs/                   # Documentación
```

## Consideraciones de Diseño

- **Modularidad**: El sistema está diseñado con componentes independientes que pueden ser mejorados o reemplazados sin afectar al resto del sistema.
- **Escalabilidad**: La arquitectura permite procesar múltiples documentos y expandir las capacidades de búsqueda.
- **Mantenibilidad**: El código está organizado en módulos con responsabilidades claras y bien documentadas.
- **Rendimiento**: Se utilizan estructuras de datos eficientes para almacenar y recuperar información rápidamente.

## Limitaciones Actuales

- El sistema actualmente procesa un documento a la vez.
- No incluye generación de respuestas en lenguaje natural.
- La interfaz es de línea de comandos, sin interfaz gráfica o web.
- No tiene capacidad de aprendizaje continuo o retroalimentación.

Para más detalles sobre componentes específicos, consulte los siguientes documentos:
- [Diagrama y descripción de componentes](diagrama_componentes.md)
- [Flujo de datos en el sistema](flujo_datos.md)
