import json
import os
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Ruta al archivo JSON con los chunks
    ruta_chunks = "data/processed/chunks.json"
    logger.info(f"Leyendo chunks desde {ruta_chunks}...")

    # Leer los chunks desde el JSON
    with open(ruta_chunks, "r", encoding="utf-8") as archivo:
        data = json.load(archivo)

    # Extraer los textos y metadatos
    logger.info("Extrayendo textos y metadatos...")
    texts = [chunk["texto"] for chunk in data]
    metadatas = [{"id": chunk["id"]} for chunk in data]

    # Generar embeddings usando TF-IDF
    logger.info("Generando embeddings con TF-IDF...")
    vectorizer = TfidfVectorizer(max_features=512)
    embeddings = vectorizer.fit_transform(texts)

    # Crear el índice usando NearestNeighbors
    logger.info("Creando índice de vectores...")
    index = NearestNeighbors(n_neighbors=5, metric='cosine')
    index.fit(embeddings)

    # Crear directorio si no existe
    os.makedirs("data/vectorstore", exist_ok=True)

    # Guardar el índice, embeddings y metadatos
    logger.info("Guardando índice y datos...")
    with open("data/vectorstore/vectorstore.pkl", "wb") as f:
        pickle.dump({
            "index": index,
            "vectorizer": vectorizer,
            "texts": texts,
            "metadatas": metadatas
        }, f)

    logger.info("Vectorstore creado y guardado exitosamente")

except Exception as e:
    logger.error(f"Error durante la ejecución: {str(e)}")
    raise
