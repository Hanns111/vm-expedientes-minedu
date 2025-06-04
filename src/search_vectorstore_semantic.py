import pickle
from sentence_transformers import SentenceTransformer
import numpy as np

VECTORSTORE_PATH = "data/processed/vectorstore_semantic.pkl"

# FUNCION REUTILIZABLE
def search_query(query):
    with open(VECTORSTORE_PATH, "rb") as f:
        data = pickle.load(f)

    index = data["index"]
    embeddings = data["embeddings"]
    chunks = data["chunks"]

    model = SentenceTransformer("all-MiniLM-L6-v2")

    query_embedding = model.encode([query])
    distances, indices = index.kneighbors(query_embedding)

    results = []
    for rank, idx in enumerate(indices[0]):
        results.append({
            "rank": rank + 1,
            "similarity": 1 - distances[0][rank],
            "text": chunks[idx]["texto"]
        })
    return results

if __name__ == "__main__":
    query = "tope diario de viáticos"
    print(f"\n🔎 Consulta de prueba: {query}")
    results = search_query(query)
    print("\n📌 Resultados más cercanos:")
    for res in results:
        print(f"\n#{res['rank']} – (similitud: {res['similarity']:.2f})")
        print(res["text"][:1000])  # muestra los primeros 1000 caracteres
