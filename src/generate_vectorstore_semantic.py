import os
import json
import logging
import pickle
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHUNKS_PATH = "data/processed/chunks.json"
VECTORSTORE_PATH = "data/processed/vectorstore_semantic.pkl"

def load_chunks(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    logger.info("📦 Cargando chunks desde %s...", CHUNKS_PATH)
    chunks = load_chunks(CHUNKS_PATH)

    # Validar que los chunks tengan contenido en la clave 'texto'
    chunks_validos = [c for c in chunks if isinstance(c, dict) and "texto" in c and c["texto"].strip()]
    
    if not chunks_validos:
        logger.error("❌ No hay chunks válidos con la clave 'texto'. Revisa el archivo JSON.")
        return
    
    textos = [chunk["texto"] for chunk in chunks_validos]

    logger.info("🧠 Cargando modelo de embeddings semánticos...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    logger.info("🔢 Generando embeddings...")
    embeddings = model.encode(textos, show_progress_bar=True)

    logger.info("🔍 Construyendo índice semántico...")
    index = NearestNeighbors(n_neighbors=5, metric="cosine")
    index.fit(embeddings)

    logger.info("💾 Guardando índice y chunks válidos en %s", VECTORSTORE_PATH)
    with open(VECTORSTORE_PATH, "wb") as f:
        pickle.dump({
            "index": index,
            "embeddings": embeddings,
            "chunks": chunks_validos
        }, f)

    logger.info("✅ Vectorstore semántico creado y guardado correctamente.")

if __name__ == "__main__":
    main()
