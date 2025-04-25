import pickle
from sentence_transformers import SentenceTransformer
import numpy as np

VECTORSTORE_PATH = "data/processed/vectorstore_semantic.pkl"

def main():
    print("🔁 Cargando vectorstore desde:", VECTORSTORE_PATH)
    with open(VECTORSTORE_PATH, "rb") as f:
        data = pickle.load(f)

    index = data["index"]
    embeddings = data["embeddings"]
    chunks = data["chunks"]

    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Consulta fija para pruebas
    query = "tope diario de viáticos"
    print(f"\n🔎 Consulta de prueba: {query}")

    query_embedding = model.encode([query])
    distances, indices = index.kneighbors(query_embedding)

    print("\n📌 Resultados más cercanos:")
    for rank, idx in enumerate(indices[0]):
        print(f"\n#{rank + 1} – (similitud: {1 - distances[0][rank]:.2f})")
        print(chunks[idx]["texto"][:1000])  # muestra los primeros 1000 caracteres

if __name__ == "__main__":
    main()
