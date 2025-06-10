# Corrección del PDF Fuente y Regeneración de Datos

**Fecha:** 2025-06-05  
**Autor:** Equipo de Desarrollo  
**Prioridad:** Alta  

## Problema Identificado

Se detectó que el sistema estaba utilizando un PDF con OCR corrupto como fuente de datos para el procesamiento de la Directiva N° 011-2020-MINEDU. Este problema afectaba la calidad de los chunks generados y, por consiguiente, la precisión de las búsquedas en los vectorstores.

## Archivos PDF Disponibles

En el directorio `data/raw/` se identificaron dos archivos PDF:

1. `DIRECTIVA N° 011-2020-MINEDU_LIMPIA.pdf` (211 KB) - PDF limpio y legible
2. `Directiva_Viatcos_011_2020.pdf` (16 MB) - PDF con OCR corrupto

## Proceso de Corrección

### 1. Extracción de Texto del PDF Limpio

Se utilizó el script `src/text_processor/pdf_extractor.py` para extraer el texto del PDF limpio:

```bash
python src/text_processor/pdf_extractor.py --input "data/raw/DIRECTIVA N° 011-2020-MINEDU_LIMPIA.pdf" --output "data/raw/resultado_limpio.txt"
```

El texto extraído se verificó y confirmó que era coherente y libre de corrupción.

### 2. Preparación para el Procesamiento

Se copió el texto extraído a la ubicación esperada por el chunker:

```bash
copy "data/raw/resultado_limpio.txt" "data/processed/texto_limpio.txt"
```

### 3. Corrección de Scripts

Se identificaron problemas con caracteres emoji en los scripts de procesamiento, que causaban errores de codificación en Windows. Se corrigieron los siguientes archivos:

- `src/text_processor/text_chunker_v2.py`
- `src/ai/generate_vectorstore_full_v2.py`

### 4. Regeneración de Chunks

Se ejecutó el script de chunking para generar nuevos chunks a partir del texto limpio:

```bash
python src/text_processor/text_chunker_v2.py
```

Se generaron 115 chunks en el archivo `data/processed/chunks_v2.json`.

### 5. Regeneración de Vectorstores

#### 5.1 Backup de Datos Antiguos

Antes de regenerar los vectorstores, se creó un backup de los archivos existentes:

```bash
mkdir -p data/processed/backup
copy data/processed/chunks_v2.json data/processed/backup/
copy data/processed/vectorstore_semantic_full_v2.pkl data/processed/backup/
copy data/processed/vectorstore_bm25_test.pkl data/processed/backup/
```

#### 5.2 Regeneración del Vectorstore TF-IDF

Se ejecutó el script para regenerar el vectorstore TF-IDF:

```bash
python src/ai/generate_vectorstore_full_v2.py
```

#### 5.3 Regeneración del Vectorstore BM25

Se ejecutó el script para regenerar el vectorstore BM25:

```bash
python src/ai/generate_vectorstore_bm25.py
```

### 6. Mejoras en el Sistema BM25

Durante las pruebas, se identificaron problemas con el sistema de búsqueda BM25, que no estaba devolviendo resultados para las consultas. Se implementaron las siguientes mejoras:

1. Mejora en el preprocesamiento de texto para normalizar acentos y caracteres especiales
2. Implementación de tokenización consistente entre la generación del índice y las búsquedas
3. Almacenamiento del corpus tokenizado en el vectorstore para referencia

Estas mejoras permitieron que el sistema BM25 funcionara correctamente y devolviera resultados relevantes.

## Validación de Resultados

Se utilizó el script `src/ai/compare_tfidf_bm25.py` para comparar los resultados de búsqueda entre los sistemas TF-IDF y BM25. Se probaron las siguientes consultas:

1. "¿Cuál es el procedimiento para solicitar viáticos?"
2. "¿Cuál es el monto máximo para viáticos?"
3. "¿Qué documentos requiere la solicitud?"
4. "¿Cuánto tiempo antes debo solicitar viáticos?"

### Resultados de las Pruebas

- Ambos sistemas (TF-IDF y BM25) devolvieron resultados relevantes para todas las consultas
- El sistema BM25 fue consistentemente más rápido que TF-IDF (entre 50% y 68% más rápido)
- Los resultados principales coincidieron entre ambos sistemas para todas las consultas
- El sistema BM25 tiende a devolver menos resultados pero más precisos
- El texto de los resultados es coherente y no muestra signos de corrupción

## Conclusiones

1. Se identificó y corrigió con éxito el problema del PDF corrupto
2. Se regeneraron todos los datos derivados (chunks y vectorstores)
3. Se mejoraron los scripts de procesamiento para mayor robustez
4. Se validó que los sistemas de búsqueda funcionan correctamente con los nuevos datos
5. El sistema ahora está listo para continuar con la siguiente fase de desarrollo

## Lecciones Aprendidas

1. Importancia de verificar la calidad de los datos fuente antes del procesamiento
2. Necesidad de implementar validaciones de calidad en los datos extraídos
3. Conveniencia de mantener backups de los datos procesados
4. Importancia de la normalización y preprocesamiento consistente del texto para búsquedas efectivas

## Próximos Pasos

1. Implementar validaciones automáticas de calidad para futuros documentos
2. Considerar la integración de técnicas de corrección automática de texto
3. Evaluar el rendimiento de los sistemas de búsqueda con consultas más complejas
4. Documentar los parámetros óptimos para el procesamiento de documentos similares
