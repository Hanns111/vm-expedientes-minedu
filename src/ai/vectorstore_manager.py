# src/ai/vectorstore_manager.py
import json
import pickle
import os
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

# Intentar importar desde la ubicación correcta de settings
try:
    from config.settings import CHUNKS_PATH, VECTORSTORE_PATH, PROCESSED_DATA_DIR
except ModuleNotFoundError:
    # Fallback para ejecución directa del script o si la estructura aún no está en PYTHONPATH
    import sys
    # Añadir el directorio raíz del proyecto al sys.path
    # Esto asume que vectorstore_manager.py está en src/ai/
    # y que config/ está en la raíz del proyecto junto a src/
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
    sys.path.append(project_root)
    from config.settings import CHUNKS_PATH, VECTORSTORE_PATH, PROCESSED_DATA_DIR

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_vectorstore(tfidf_max_features=None, nn_n_neighbors=5):
    """
    Genera un vectorstore a partir de los chunks procesados y lo guarda.

    Args:
        tfidf_max_features (int, optional): Número máximo de features para TfidfVectorizer.
                                            Defaults to None (sin límite).
        nn_n_neighbors (int, optional): Número de vecinos para NearestNeighbors.
                                        Defaults to 5.
    """
    try:
        logger.info(f"Iniciando la generación del vectorstore.")
        logger.info(f"Cargando chunks desde: {CHUNKS_PATH}")

        if not os.path.exists(CHUNKS_PATH):
            logger.error(f"Archivo de chunks no encontrado en {CHUNKS_PATH}. "
                         "Asegúrate de generar los chunks primero (ej: chunks_consolidated.json).")
            return False

        with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
            chunks_data = json.load(f)

        if not chunks_data:
            logger.error("El archivo de chunks está vacío.")
            return False

        # Asumimos que chunks_data es una lista de diccionarios, cada uno con una clave 'texto'
        texts = [chunk["texto"] for chunk in chunks_data if "texto" in chunk]
        if not texts:
            logger.error("No se encontraron textos en los chunks. Verifica el formato de chunks.json.")
            return False
        
        logger.info(f"Se encontraron {len(texts)} textos para procesar.")

        # Generar embeddings con TF-IDF
        logger.info(f"Generando embeddings con TF-IDF (max_features={tfidf_max_features})...")
        vectorizer = TfidfVectorizer(max_features=tfidf_max_features)
        embeddings = vectorizer.fit_transform(texts)
        logger.info(f"Dimensiones de la matriz de embeddings: {embeddings.shape}")

        # Crear el índice de búsqueda semántica
        logger.info(f"Creando índice de búsqueda con NearestNeighbors (n_neighbors={nn_n_neighbors}, metric='cosine')...")
        nn_index = NearestNeighbors(n_neighbors=nn_n_neighbors, metric="cosine")
        nn_index.fit(embeddings)

        # Asegurarse de que el directorio de salida exista
        os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

        # Guardar el vectorstore consolidado
        vectorstore_content = {
            "chunks": chunks_data,  # Guardamos los chunks completos
            "vectorizer": vectorizer,
            "index": nn_index
        }

        logger.info(f"Guardando vectorstore en: {VECTORSTORE_PATH}")
        with open(VECTORSTORE_PATH, "wb") as f:
            pickle.dump(vectorstore_content, f)

        logger.info(f"✅ Vectorstore generado y guardado exitosamente en: {VECTORSTORE_PATH}")
        return True

    except Exception as e:
        logger.error(f"Error durante la generación del vectorstore: {e}", exc_info=True)
        return False

def load_vectorstore():
    """
    Carga el vectorstore desde el archivo.

    Returns:
        dict: El contenido del vectorstore, o None si no se encuentra o hay un error.
    """
    try:
        logger.info(f"Cargando vectorstore desde: {VECTORSTORE_PATH}")
        if not os.path.exists(VECTORSTORE_PATH):
            logger.error(f"Archivo de vectorstore no encontrado en {VECTORSTORE_PATH}")
            return None
        
        with open(VECTORSTORE_PATH, "rb") as f:
            vectorstore_content = pickle.load(f)
        logger.info("Vectorstore cargado exitosamente.")
        return vectorstore_content
    except Exception as e:
        logger.error(f"Error al cargar el vectorstore: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    # Esto permitirá ejecutar el script directamente para generar el vectorstore
    # Asegúrate de que 'chunks_consolidated.json' exista en la ruta correcta
    # definida en config/settings.py (CHUNKS_PATH)
    
    # Ejemplo de cómo podrías querer ejecutarlo:
    # if os.path.exists(CHUNKS_PATH):
    #    generate_vectorstore(tfidf_max_features=5000, nn_n_neighbors=5)
    # else:
    #    logger.error(f"No se puede generar el vectorstore porque {CHUNKS_PATH} no existe.")
    #    logger.info("Por favor, primero genera el archivo de chunks consolidado.")
    
    logger.info("Ejecutando vectorstore_manager.py como script principal.")
    logger.info(f"Este script espera que {CHUNKS_PATH} exista.")
    logger.info("Si deseas generar el vectorstore, descomenta y ajusta las líneas en la sección if __name__ == '__main__'.")
    logger.info("Por ejemplo, para generar con valores por defecto (si los chunks existen):")
    logger.info("# generate_vectorstore()")
    # generate_vectorstore() # Descomentar para ejecutar la generación
