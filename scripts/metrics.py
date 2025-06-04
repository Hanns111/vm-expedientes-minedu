import sys
import os
import time
import json

# Asegura que podamos importar desde la raíz del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.search_vectorstore_semantic import search_query

# Ruta al archivo de chunks
CHUNKS_FILE = "data/processed/chunks.json"

def count_chunks():
    with open(CHUNKS_FILE, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    return len(chunks)

def measure_avg_time(query_text: str, runs: int = 5):
    times = []
    for _ in range(runs):
        t0 = time.time()
        _ = search_query(query_text)
        times.append(time.time() - t0)
    return sum(times) / len(times)

if __name__ == "__main__":
    print("📦 Métricas de desempeño del asistente IA\n")

    # Contar chunks
    total_chunks = count_chunks()
    print(f"✅ Total de chunks procesados: {total_chunks}")

    # Medir tiempo promedio local
    sample_query = "tope diario de viáticos"
    avg_local = measure_avg_time(sample_query, runs=5)
    print(f"⏱ Tiempo promedio local (5 runs): {avg_local:.3f} segundos")

    # Aquí puedes agregar en el futuro precisión/recall sobre un set de validación
    print("\n📊 (Opcional futuro) Precisión y recall aún no implementados.")
