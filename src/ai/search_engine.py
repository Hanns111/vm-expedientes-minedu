# src/ai/search_engine.py
import os
import sys
import pickle
import re
import logging

# Ajustar sys.path para importar módulos del proyecto
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(project_root)

try:
    from config.settings import SPACY_MODEL_NAME # Para EntitiesExtractor
    from src.ai.vectorstore_manager import load_vectorstore
    # Asumimos que entities_extractor.py está en el mismo directorio src/ai/
    # o que se ha movido a una ubicación accesible y se importa correctamente.
    # Si entities_extractor.py se mueve, esta importación necesitará ajuste.
    from entities_extractor import EntitiesExtractor 
except ModuleNotFoundError as e:
    print(f"Error de importación en search_engine.py: {e}")
    print("Asegúrate de que config/settings.py y src/ai/vectorstore_manager.py existan.")
    print("Y que entities_extractor.py esté en src/ai/ o en el PYTHONPATH.")
    sys.exit(1)

# sklearn es necesario si el vectorizador es TfidfVectorizer
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity # No usado directamente aquí pero relacionado
except ImportError:
    TfidfVectorizer = None # Marcar como no disponible si sklearn no está

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SearchEngine:
    def __init__(self):
        logger.info("Inicializando SearchEngine...")
        self.vectorstore_data = load_vectorstore()
        if not self.vectorstore_data:
            logger.error("No se pudo cargar el vectorstore. SearchEngine no puede operar.")
            raise ValueError("Error al cargar el vectorstore.")

        self.chunks = self.vectorstore_data.get('chunks')
        self.embeddings = self.vectorstore_data.get('embeddings') # Podría no ser usado directamente si el índice ya está construido
        self.index = self.vectorstore_data.get('index') # Modelo NearestNeighbors
        self.vectorizer = self.vectorstore_data.get('vectorizer') # Puede ser TfidfVectorizer o SentenceTransformer

        if not all([self.chunks, self.index, self.vectorizer]):
            logger.error("Componentes del vectorstore faltantes. Chunks, index y vectorizer son requeridos.")
            raise ValueError("Componentes del vectorstore incompletos.")

        # Determinar el tipo de vectorizador/modelo de embedding
        if hasattr(self.vectorizer, 'transform') and TfidfVectorizer and isinstance(self.vectorizer, TfidfVectorizer):
            self.embedding_mode = 'tfidf'
            logger.info("Modo de embedding: TF-IDF (sklearn).")
        elif hasattr(self.vectorizer, 'encode'):
            self.embedding_mode = 'sentence_transformer'
            logger.info("Modo de embedding: SentenceTransformer.")
        else:
            logger.error("Tipo de vectorizador no reconocido. Debe tener método 'transform' o 'encode'.")
            raise TypeError("Vectorizador no compatible.")

        try:
            # EntitiesExtractor podría necesitar el nombre del modelo spacy desde config
            self.entities_extractor = EntitiesExtractor(model_name=SPACY_MODEL_NAME)
            logger.info(f"EntitiesExtractor inicializado con modelo: {SPACY_MODEL_NAME}")
        except Exception as e:
            logger.error(f"Error al inicializar EntitiesExtractor: {e}")
            # Podríamos decidir si esto es un error fatal o si el SearchEngine puede funcionar sin él
            self.entities_extractor = None 
            logger.warning("EntitiesExtractor no pudo ser inicializado. La extracción de entidades no estará disponible.")
        
        logger.info("SearchEngine inicializado correctamente.")

    def _process_query_embedding(self, query_text):
        if self.embedding_mode == 'tfidf':
            return self.vectorizer.transform([query_text])
        elif self.embedding_mode == 'sentence_transformer':
            return self.vectorizer.encode([query_text])
        return None

    def _is_relevant(self, texto_chunk, query_text):
        """Determina si un texto es relevante para la consulta (lógica de search_vectorstore_hybrid.py)"""
        texto_lower = texto_chunk.lower()
        query_lower = query_text.lower()
        
        # Palabras clave específicas (ejemplo para 'fecha de publicación')
        # Esto debería ser más dinámico o general en una implementación avanzada
        palabras_clave = ['fecha', 'publicación', 'emisión', 'vigencia', 'aprobación', 'promulgación', 'norma', 'directiva']
        
        patrones_fecha = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # dd/mm/yyyy o dd-mm-yy
            r'\b\d{1,2}\s+de\s+[a-zA-ZáéíóúÁÉÍÓÚñÑ]+\s+de\s+\d{2,4}\b',  # dd de mes de yyyy
            r'\b[a-zA-ZáéíóúÁÉÍÓÚñÑ]+\s+\d{1,2}(?:,\s*|\s+de\s+)\d{2,4}\b' # Mes dd, yyyy
        ]
        
        tiene_claves_query = any(palabra_query in texto_lower for palabra_query in query_lower.split() if len(palabra_query) > 2)
        tiene_palabras_relevantes = any(clave in texto_lower for clave in palabras_clave)
        tiene_fechas_en_chunk = any(re.search(patron, texto_lower) for patron in patrones_fecha)

        # Criterio de relevancia: debe contener alguna palabra de la query Y
        # (alguna palabra clave general O alguna fecha)
        # Este criterio es un ejemplo y puede necesitar muchos ajustes.
        es_relevante_flag = tiene_claves_query and (tiene_palabras_relevantes or tiene_fechas_en_chunk)
        
        # logger.debug(f"Relevance check for query '{query_text}' in chunk: Relevant={es_relevante_flag}, HasQueryTerms={tiene_claves_query}, HasKeywords={tiene_palabras_relevantes}, HasDates={tiene_fechas_en_chunk}")
        return es_relevante_flag

    def _generate_response_from_entities(self, entidades):
        """Genera una respuesta organizada basada en las entidades encontradas."""
        respuesta = []
        if not entidades:
            return "No se extrajeron entidades específicas del texto."

        if entidades.get("fechas"):
            fechas_str = [f["valor"] for f in entidades["fechas"]]
            if fechas_str:
                respuesta.append(f"Fechas encontradas: {', '.join(fechas_str)}")
        
        if entidades.get("montos"):
            montos_str = [m["valor"] for m in entidades["montos"]]
            if montos_str:
                respuesta.append(f"Montos encontrados: {', '.join(montos_str)}")
        
        if entidades.get("numerales"):
            numerales_str = [n["valor"] for n in entidades["numerales"]]
            if numerales_str:
                respuesta.append(f"Numerales/Artículos encontrados: {', '.join(numerales_str)}")
        
        if entidades.get("expedientes"):
            expedientes_str = [e["valor"] for e in entidades["expedientes"]]
            if expedientes_str:
                respuesta.append(f"Números de expediente encontrados: {', '.join(expedientes_str)}")
        
        if entidades.get("entidades"): # Entidades nombradas (ORG, PER, LOC, MISC)
            ent_nombradas_str = [f"{e['valor']} ({e['tipo']})" for e in entidades["entidades"]]
            # Filtrar por relevancia si es necesario, ej: directivas, normativas
            # entidades_rel = [e['valor'] for e in entidades["entidades"] if "directiva" in e['valor'].lower() or "normativa" in e['valor'].lower()]
            if ent_nombradas_str:
                 respuesta.append(f"Otras entidades mencionadas: {', '.join(ent_nombradas_str)}")

        return "\n".join(respuesta) if respuesta else "No se encontraron datos clave estructurados en el texto."

    def search(self, query_text, top_n=5, apply_relevance_filter=True):
        logger.info(f"Iniciando búsqueda para: \"{query_text}\", top_n={top_n}, filtro_relevancia={apply_relevance_filter}")
        
        query_embedding = self._process_query_embedding(query_text)
        if query_embedding is None:
            logger.error("No se pudo generar el embedding para la consulta.")
            return {"error": "Fallo al procesar la consulta."}

        try:
            # El índice (nn_model) espera un array 2D, incluso para una sola consulta
            distances, sem_indices = self.index.kneighbors(query_embedding, n_neighbors=min(top_n * 2, len(self.chunks))) # Pedir más para filtrar
        except Exception as e:
            logger.error(f"Error durante la búsqueda k-NN: {e}")
            return {"error": "Fallo en la búsqueda por similitud."}
            
        # sem_indices[0] porque solo tenemos una consulta
        semantic_results_chunks = [self.chunks[i] for i in sem_indices[0]]
        
        final_results_data = []

        if apply_relevance_filter:
            logger.info("Aplicando filtro de relevancia...")
            relevant_results_chunks = [
                chunk for chunk in semantic_results_chunks if self._is_relevant(chunk.get('texto', ''), query_text)
            ]
            logger.info(f"Resultados relevantes encontrados: {len(relevant_results_chunks)}")
            
            if relevant_results_chunks:
                # Tomar hasta top_n de los relevantes
                final_results_data = relevant_results_chunks[:top_n]
            else:
                logger.warning("No se encontraron resultados relevantes con el filtro. Usando los más cercanos semánticamente.")
                # Si no hay relevantes, tomar los top_n semánticos (fallback)
                final_results_data = semantic_results_chunks[:top_n]
        else:
            logger.info("Filtro de relevancia desactivado. Usando los más cercanos semánticamente.")
            final_results_data = semantic_results_chunks[:top_n]

        if not final_results_data:
            logger.warning("No se encontraron resultados para la consulta.")
            return {"message": "No se encontraron resultados.", "results": []}

        # Procesar resultados para la salida
        output_results = []
        for i, chunk_data in enumerate(final_results_data):
            texto_completo_chunk = chunk_data.get('texto', '')
            titulo_chunk = chunk_data.get('titulo', f"Chunk {chunk_data.get('id', i+1)}")
            
            extracted_entities_info = "Extracción de entidades no disponible."
            if self.entities_extractor:
                try:
                    entities = self.entities_extractor.extract_entities(texto_completo_chunk)
                    extracted_entities_info = self._generate_response_from_entities(entities)
                except Exception as e:
                    logger.error(f"Error extrayendo entidades del chunk '{titulo_chunk}': {e}")
            
            output_results.append({
                "rank": i + 1,
                "titulo_chunk": titulo_chunk,
                "texto_chunk_snippet": texto_completo_chunk[:300] + "...", # Snippet
                "texto_completo_chunk": texto_completo_chunk, # Para posible visualización completa
                "extracted_entities_summary": extracted_entities_info,
                "id_chunk": chunk_data.get('id')
            })
        
        logger.info(f"Búsqueda completada. {len(output_results)} resultados procesados.")
        return {
            "query": query_text,
            "message": f"Se encontraron {len(output_results)} resultados.",
            "results": output_results
        }

if __name__ == "__main__":
    logger.info("Ejecutando SearchEngine como script principal para prueba...")
    
    # Crear una instancia del motor de búsqueda
    # Esto cargará el vectorstore y el extractor de entidades
    try:
        engine = SearchEngine()
    except Exception as e:
        logger.error(f"No se pudo inicializar SearchEngine para la prueba: {e}")
        sys.exit(1)

    # Consulta de ejemplo
    # query_de_prueba = "fecha de publicación de la directiva de viáticos"
    # query_de_prueba = "cuál es el procedimiento para la rendición de viáticos"
    query_de_prueba = "normativa sobre comisiones de servicio"

    logger.info(f"\n--- Probando búsqueda con consulta: '{query_de_prueba}' ---")
    resultados = engine.search(query_de_prueba, top_n=3, apply_relevance_filter=True)

    if resultados.get("error"):
        logger.error(f"Error en la búsqueda: {resultados['error']}")
    elif not resultados.get("results"):
        logger.info("No se encontraron resultados para la consulta de prueba.")
    else:
        print(f"\nResultados para la consulta: \"{resultados['query']}\"")
        print(resultados['message'])
        for res in resultados['results']:
            print(f"\nRank {res['rank']}: {res['titulo_chunk']}")
            print(f"  Snippet: {res['texto_chunk_snippet']}")
            print(f"  Entidades extraídas:\n    {res['extracted_entities_summary'].replace(chr(10), chr(10) + '    ')}") # Indentar
            print(f"  ID Chunk: {res['id_chunk']}")
        print("\n--- Fin de la prueba ---")

    # Prueba con filtro de relevancia desactivado
    logger.info(f"\n--- Probando búsqueda SIN FILTRO con consulta: '{query_de_prueba}' ---")
    resultados_sin_filtro = engine.search(query_de_prueba, top_n=2, apply_relevance_filter=False)
    if resultados_sin_filtro.get("error"):
        logger.error(f"Error en la búsqueda sin filtro: {resultados_sin_filtro['error']}")
    elif not resultados_sin_filtro.get("results"):
        logger.info("No se encontraron resultados para la consulta de prueba sin filtro.")
    else:
        print(f"\nResultados para la consulta (sin filtro): \"{resultados_sin_filtro['query']}\"")
        print(resultados_sin_filtro['message'])
        for res in resultados_sin_filtro['results']:
            print(f"\nRank {res['rank']}: {res['titulo_chunk']}")
            print(f"  Snippet: {res['texto_chunk_snippet']}")
            print(f"  ID Chunk: {res['id_chunk']}")
        print("\n--- Fin de la prueba (sin filtro) ---")
