import json
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from sentence_transformers import SentenceTransformer

# Cargar los chunks desde el JSON
with open('data/processed/chunks_v2.json', 'r', encoding='utf-8') as f:
    chunks = json.load(f)

# Extraer solo el texto si los chunks son diccionarios con metadatos
texts = [chunk['texto'] if isinstance(chunk, dict) else chunk for chunk in chunks]

# Generar embeddings semánticos
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = embedding_model.encode(texts)

# Crear el índice de búsqueda semántica
nn_model = NearestNeighbors(n_neighbors=3, metric='cosine')
nn_model.fit(embeddings)

# Guardar todo en un vectorstore robusto
vectorstore = {
    'chunks': chunks,
    'embeddings': embeddings,
    'nn_model': nn_model,
    'embedding_model': embedding_model
}

with open('data/processed/vectorstore_semantic_full_v2.pkl', 'wb') as f:
    pickle.dump(vectorstore, f)

print("✅ Vectorstore robusto generado y guardado en: data/processed/vectorstore_semantic_full_v2.pkl")
