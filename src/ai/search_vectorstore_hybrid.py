import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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
query_embedding = embedding_model.transform([query])   # Usamos transform para TF-IDF
_, sem_index = nn_model.kneighbors(query_embedding, n_neighbors=1)
sem_result = chunks[sem_index[0][0]]

# --- Búsqueda TF-IDF ---
query_tfidf = tfidf_vectorizer.transform([query])
cos_similarities = cosine_similarity(query_tfidf, tfidf_matrix).flatten()
tfidf_index = cos_similarities.argmax()
tfidf_result = chunks[tfidf_index]

# Mostrar resultados
print("\n📘 Resultado Semántico:")
print(sem_result)

print("\n📗 Resultado TF-IDF:")
print(tfidf_result)

# Confirmar coincidencia
if sem_index[0][0] == tfidf_index:
    print("\n✅ Ambos métodos coinciden.")
else:
    print("\n⚠ Los métodos dieron resultados distintos.")
