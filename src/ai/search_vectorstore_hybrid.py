import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from extract_entities import extract_entities

def generar_respuesta(entidades):
    respuesta = ""

    if entidades["numerales"]:
        respuesta += f"Según {entidades['numerales'][0]}, "
   
    if entidades["montos"]:
        respuesta += f"el monto indicado es {entidades['montos'][0]}. "
   
    if entidades["fechas"]:
        respuesta += f"(Vigente desde {entidades['fechas'][0]})"
   
    return respuesta if respuesta else "No se encontraron datos clave en el texto."

# Cargar el vectorstore robusto
with open('data/processed/vectorstore_semantic_full_v2.pkl', 'rb') as f:
    vectorstore = pickle.load(f)

chunks = vectorstore['chunks']
embeddings = vectorstore['embeddings']
nn_model = vectorstore['nn_model']
embedding_model = vectorstore['embedding_model']

# Preparar textos para TF-IDF
texts = [chunk['texto'] if isinstance(chunk, dict) else chunk for chunk in chunks]
tfidf_vectorizer = TfidfVectorizer()
tfidf_matrix = tfidf_vectorizer.fit_transform(texts)

# Solicitar consulta al usuario
query = input("\n🔎 Ingresa tu consulta normativa: ")

# --- Búsqueda Semántica ---
query_embedding = embedding_model.transform([query])
_, sem_index = nn_model.kneighbors(query_embedding, n_neighbors=1)
sem_result = chunks[sem_index[0][0]]

# --- Búsqueda TF-IDF ---
query_tfidf = tfidf_vectorizer.transform([query])
cos_similarities = cosine_similarity(query_tfidf, tfidf_matrix).flatten()
tfidf_index = cos_similarities.argmax()
tfidf_result = chunks[tfidf_index]

# Confirmar coincidencia
if sem_index[0][0] == tfidf_index:
    print("\n✅ Ambos métodos coinciden.")
else:
    print("\n⚠ Los métodos dieron resultados distintos.")
# Aplicar extracción de entidades al resultado semántico
entidades = extract_entities(sem_result['texto'])

print("\n==============================")
print("🔎 Respuesta Inteligente:")
print(generar_respuesta(entidades))
print("==============================")
