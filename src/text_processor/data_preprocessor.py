# src/text_processor/data_preprocessor.py
import re
import unicodedata
import json
import os
import logging
import uuid # Para generar IDs únicos para los chunks

# Intentar importar desde la ubicación correcta de settings
try:
    from config.settings import RAW_TEXT_INPUT_PATH, CHUNKS_PATH, PROCESSED_DATA_DIR
except ModuleNotFoundError:
    import sys
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
    sys.path.append(project_root)
    from config.settings import RAW_TEXT_INPUT_PATH, CHUNKS_PATH, PROCESSED_DATA_DIR

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Funciones de Limpieza (adaptadas de text_cleaner_avanzado.py) ---
def normalizar_texto(texto):
    texto = unicodedata.normalize('NFC', texto)
    texto = texto.replace('\uFFFD', ' ') # Explicitly replace REPLACEMENT CHARACTER

    # Keep letters (including Spanish), numbers, newline, and a specific set of punctuation.
    # Allowed punctuation: . , ; : ( ) - /
    allowed_chars_pattern = r'[^a-zA-Z0-9áéíóúüÁÉÍÓÚÜñÑ\s\n\.,;:\(\)\-\/]'
    texto = re.sub(allowed_chars_pattern, ' ', texto, flags=re.UNICODE)
    
    # Collapse multiple spaces introduced by replacements
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def corregir_espacios(texto):
    # Corregir palabras con espacios entre letras (ej. p a l a b r a -> palabra)
    # Esta lista puede expandirse o hacerse configurable
    palabras_comunes = [
        'ministerio', 'educacion', 'directiva', 'procedimiento', 'administrativo',
        'documento', 'normativo', 'viaticos', 'pasajes', 'comision', 'servicio',
        'nacional', 'general', 'oficina', 'administracion', 'contabilidad',
        'presupuesto', 'tesoreria', 'coordinacion', 'financiera', 'control',
        'previo', 'abastecimiento', 'unidad', 'ejecutora', 'organica', 'fecha',
        'publicacion', 'emision', 'vigencia', 'aprobacion', 'resolucion',
        'considerando', 'articulo', 'secretaria', 'direccion', 'informe', 'tecnico',
        'legal', 'numero', 'anexo', 'referencia', 'solicitud', 'apruebese', 'registrese',
        'comuniquese', 'publiquese', 'finalidad', 'objetivo', 'alcance', 'base',
        'responsabilidades', 'disposiciones', 'generales', 'especificas', 'complementarias',
        'transitorias', 'derogatorias', 'finales', 'glosario', 'terminos', 'flujograma'
    ]
    for palabra in palabras_comunes:
        if not palabra: continue # Skip empty strings if any
        # Pattern for "p a l a b r a", ensuring it's a whole word match
        spaced_palabra = palabra[0] + ''.join(r'\s+' + re.escape(letra) for letra in palabra[1:])
        patron = r'\b' + spaced_palabra + r'\b'
        try:
            texto = re.sub(patron, palabra, texto, flags=re.IGNORECASE)
        except re.error as e:
            logger.warning(f"Regex error with word '{palabra}': {e}")
    
    patrones_especificos = [
        (r'M\s*I\s*N\s*E\s*D\s*U', 'MINEDU'),
        (r'(\d+)\s*/\s*(\d+)\s*/\s*(\d+)', r'\1/\2/\3'), # Fechas
        (r'(\d+)\s+(\.\s*\d+)', r'\1\2'), # Números decimales
    ]
    for patron, reemplazo in patrones_especificos:
        texto = re.sub(patron, reemplazo, texto)
    
    texto = re.sub(r'\s+([.,;:?!)])', r'\1', texto) # Espacio antes de puntuación
    texto = re.sub(r'[(]\s+', r'(', texto) # Espacio después de paréntesis de apertura
    texto = re.sub(r'\s+', ' ', texto) # Múltiples espacios a uno
    return texto

def corregir_errores_ocr(texto):
    reemplazos = [
        (r'd\s*[eE]\s*l\s*', 'del '), (r'[eE]\s*l\s+', 'el '),
        (r'0(?=[a-zA-Z])', 'o'), (r'l(?=\d)', '1'),
        (r'd\s*[i1]rect[i1]va', 'directiva'), (r'm\s*[i1]n\s*[i1]ster[i1]o', 'ministerio'),
        (r'[eE]ducac[i1][o0]n', 'Educación'), (r'publ[i1]cac[i1][o0]n', 'publicación'),
        (r'[fF][eE][cC][hH][aA]', 'fecha'),
        (r'(\d+)[/\\](\d+)[/\\](\d+)', r'\1/\2/\3'),
    ]
    for patron, reemplazo in reemplazos:
        texto = re.sub(patron, reemplazo, texto)
    return texto

def limpiar_texto_avanzado(texto):
    texto = normalizar_texto(texto)
    texto = corregir_errores_ocr(texto)
    texto = corregir_espacios(texto)
    texto = re.sub(r'\n\s*\n', '\n\n', texto) # Múltiples líneas vacías
    return texto.strip()

# --- Función de Chunking (adaptada de text_chunker_v2.py) ---
def chunkear_texto_por_titulo(texto_limpio):
    # Expresión regular para detectar títulos de secciones (ej. 1. Objeto, 2. Finalidad, etc.)
    # Este patrón puede necesitar ajustes según la estructura de tus documentos.
    patron_titulo = re.compile(r'(\b\d+\.[\d\.]*\s+[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑa-záéíóúñ\s,;:\(\)-]+)(?=\n|\Z)')
    
    chunks = []
    last_end = 0
    chunk_id_counter = 1

    # Buscar la primera sección (puede no tener título numerado)
    primer_titulo_match = patron_titulo.search(texto_limpio)
    if primer_titulo_match and primer_titulo_match.start() > 0:
        contenido_inicial = texto_limpio[0:primer_titulo_match.start()].strip()
        if contenido_inicial:
            chunks.append({
                "id": str(uuid.uuid4()),
                "chunk_order_id": chunk_id_counter,
                "titulo": "Introducción", # Título genérico
                "texto": contenido_inicial
            })
            chunk_id_counter += 1
            last_end = primer_titulo_match.start()

    # Iterar sobre los títulos encontrados
    for match in patron_titulo.finditer(texto_limpio):
        titulo = match.group(1).strip()
        start_match, end_match = match.span()

        # El contenido es desde el final del título anterior hasta el inicio del título actual
        if start_match > last_end: # Hay texto entre el título anterior y este
            contenido_previo = texto_limpio[last_end:start_match].strip()
            # Si el chunk anterior ya tenía título, este contenido es parte de ese chunk.
            # Si no, es un chunk sin título explícito (poco probable con este patrón)
            # Esta lógica podría necesitar refinamiento si los chunks no siempre empiezan con un título.
            if chunks and last_end != 0 : # Si no es el primer chunk y hubo un título antes
                 # Añadir al texto del chunk anterior si no es solo whitespace
                if contenido_previo:
                    chunks[-1]["texto"] = (chunks[-1]["texto"] + "\n\n" + contenido_previo).strip()

        # Crear el nuevo chunk con el título actual
        # El texto de este chunk se tomará hasta el siguiente título o el final del documento
        chunks.append({
            "id": str(uuid.uuid4()),
            "chunk_order_id": chunk_id_counter,
            "titulo": titulo,
            "texto": "" # Se llenará con el contenido hasta el próximo título
        })
        chunk_id_counter += 1
        last_end = end_match # El contenido del chunk actual empieza después de su título

    # Llenar el texto de los chunks
    # El texto de un chunk va desde el final de su título hasta el inicio del siguiente título
    # o hasta el final del documento para el último chunk.
    for i in range(len(chunks)):
        start_content = texto_limpio.find(chunks[i]["titulo"]) + len(chunks[i]["titulo"])
        if i + 1 < len(chunks):
            # Buscar el inicio del título del siguiente chunk
            # Es importante usar el texto original para encontrar la posición correcta del siguiente título
            end_content_search_area = texto_limpio[start_content:]
            next_title_match_in_area = patron_titulo.search(end_content_search_area)
            if next_title_match_in_area:
                end_content = start_content + next_title_match_in_area.start()
            else: # No se encontró el siguiente título, tomar hasta el final
                 end_content = len(texto_limpio)
        else:
            end_content = len(texto_limpio)
        
        chunks[i]["texto"] = texto_limpio[start_content:end_content].strip()

    # Log chunks before filtering
    logger.info(f"Chunks antes de filtrar vacíos (primeros 3 para brevedad si son muchos): {json.dumps(chunks[:3], ensure_ascii=False, indent=2)}")
    logger.info(f"Total chunks antes de filtrar: {len(chunks)}")

    # Filtrar chunks que puedan haber quedado vacíos después del procesamiento
    chunks = [chunk for chunk in chunks if chunk["texto"]]
    
    # Re-asignar chunk_order_id si se eliminaron chunks vacíos
    for i, chunk in enumerate(chunks):
        chunk["chunk_order_id"] = i + 1
        
    return chunks

# --- Función Principal de Preprocesamiento ---
def preprocess_raw_text():
    logger.info(f"Iniciando preprocesamiento de texto desde: {RAW_TEXT_INPUT_PATH}")

    if not os.path.exists(RAW_TEXT_INPUT_PATH):
        logger.error(f"Archivo de entrada no encontrado: {RAW_TEXT_INPUT_PATH}")
        return False

    try:
        with open(RAW_TEXT_INPUT_PATH, "r", encoding="utf-8", errors="ignore") as f:
            texto_original = f.read()
        logger.info("Archivo de entrada leído exitosamente.")

        texto_limpio = limpiar_texto_avanzado(texto_original)
        logger.info("Limpieza de texto completada.")
        logger.info(f"Texto limpio (primeros 500 caracteres): '{texto_limpio[:500]}'")
        logger.info(f"Longitud del texto limpio: {len(texto_limpio)}")

        chunks = chunkear_texto_por_titulo(texto_limpio)
        logger.info(f"Chunking completado. Se generaron {len(chunks)} chunks.")

        if not chunks:
            logger.warning("No se generaron chunks. El archivo de salida estará vacío o no se creará.")
            # Opcionalmente, crear un archivo JSON vacío si es el comportamiento deseado
            # os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
            # with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
            #    json.dump([], f, ensure_ascii=False, indent=2)
            return False # Indicar que no se generaron chunks útiles

        # Asegurarse de que el directorio de salida exista
        os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

        with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Chunks consolidados guardados en: {CHUNKS_PATH}")
        return True

    except Exception as e:
        logger.error(f"Error durante el preprocesamiento de texto: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    logger.info("Ejecutando data_preprocessor.py como script principal.")
    # Este script leerá de RAW_TEXT_INPUT_PATH y escribirá en CHUNKS_PATH
    # definidos en config/settings.py
    success = preprocess_raw_text()
    if success:
        logger.info("Preprocesamiento de datos completado exitosamente.")
    else:
        logger.error("Falló el preprocesamiento de datos.")
