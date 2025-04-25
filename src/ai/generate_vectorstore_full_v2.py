import json
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

# Rutas
RUTA_CHUNKS = "data/processed/chunks_v2.json"
RUTA_VECTORSTORE = "data/processed/vectorstore_semantic_full_v2.pkl"

def generate_vectorstore():
    # Cargar los chunks mejorados
    with open(RUTA_CHUNKS, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    textos = [chunk["texto"] for chunk in chunks]

    # Generar embeddings con TF-IDF
    vectorizer = TfidfVectorizer()
    embeddings = vectorizer.fit_transform(textos)

    # Crear el índice de búsqueda semántica
    index = NearestNeighbors(metric="cosine")
    index.fit(embeddings)

    # Guardar el vectorstore robusto
    vectorstore = {
        "chunks": chunks,
        "embeddings": embeddings,
        "nn_model": index,
        "embedding_model": vectorizer
    }

    with open(RUTA_VECTORSTORE, "wb") as f:
        pickle.dump(vectorstore, f)

    print(f"✅ Vectorstore robusto generado y guardado en: {RUTA_VECTORSTORE}")

if __name__ == "__main__":
    generate_vectorstore()
