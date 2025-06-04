import pickle
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from entities_extractor import EntitiesExtractor

def generar_respuesta(entidades):
    """Genera una respuesta clara y organizada basada en las entidades encontradas"""
    respuesta = []
    
    # Buscar fechas relevantes
    if entidades["fechas"]:
        fechas = [f["valor"] for f in entidades["fechas"]]
        if fechas:
            respuesta.append(f"Fechas encontradas: {', '.join(fechas)}")
    
    # Buscar montos relevantes
    if entidades["montos"]:
        montos = [m["valor"] for m in entidades["montos"]]
        if montos:
            respuesta.append(f"Montos encontrados: {', '.join(montos)}")
    
    # Buscar numerales relevantes
    if entidades["numerales"]:
        numerales = [n["valor"] for n in entidades["numerales"]]
        if numerales:
            respuesta.append(f"Numerales encontrados: {', '.join(numerales)}")
    
    # Buscar expedientes relevantes
    if entidades["expedientes"]:
        expedientes = [e["valor"] for e in entidades["expedientes"]]
        if expedientes:
            respuesta.append(f"N�meros de expediente encontrados: {', '.join(expedientes)}")
    
    # Buscar entidades nombradas relevantes
    if entidades["entidades"]:
        entidades_rel = [e for e in entidades["entidades"] if "directiva" in e.lower() or "normativa" in e.lower()]
        if entidades_rel:
            respuesta.append("\nReferencias a la normativa:")
            for entidad in entidades_rel:
                respuesta.append(f"- {entidad}")
    
    return "\n".join(respuesta) if respuesta else "No se encontraron datos clave en el texto."

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

# Usar consulta predefinida
query = "fecha de publicación de la directiva"

# --- Búsqueda Semántica ---
query_embedding = embedding_model.transform([query])
_, sem_indices = nn_model.kneighbors(query_embedding, n_neighbors=5)  # Tomar los 5 más cercanos
sem_results = [chunks[i] for i in sem_indices[0]]

# --- Filtrar resultados relevantes ---
def es_relevante(texto, query):
    """Determina si un texto es relevante para la consulta"""
    texto_lower = texto.lower()
    query_lower = query.lower()
    
    # Palabras clave específicas para la fecha de publicación
    palabras_clave = ['fecha', 'publicación', 'emisión', 'vigencia', 'aprobación', 'promulgación']
    
    # Patrones específicos para fechas
    patrones_fecha = [
        r'\b\d{2}/\d{2}/\d{4}\b',  # dd/mm/yyyy
        r'\b\d{2}\s+de\s+[a-zA-Z]+\s+de\s+\d{4}\b',  # dd de mes de yyyy
        r'\b\d{1,2}\s+[a-zA-Z]+\s+\d{4}\b'  # dd mes yyyy
    ]
    
    # Verificar si el texto contiene palabras clave y la consulta
    tiene_claves = any(palabra in texto_lower for palabra in palabras_clave)
    tiene_fechas = any(re.search(patron, texto) for patron in patrones_fecha)
    
    return tiene_claves and tiene_fechas and \
           any(palabra in texto_lower for palabra in query_lower.split())

# Filtrar resultados relevantes
relevant_results = [r for r in sem_results if es_relevante(r['texto'], query)]

if relevant_results:
    # Tomar el resultado más relevante
    final_result = relevant_results[0]
    print("\nResultado encontrado:")
    print(final_result['texto'][:500] + '...')
else:
    # Si no hay resultados relevantes, usar el más cercano
    final_result = sem_results[0]
    print("\nNo se encontraron resultados completamente relevantes, usando el más cercano:")
    print(final_result['texto'][:500] + '...')

# Inicializar el extractor de entidades
extractor = EntitiesExtractor()

# Aplicar extracción de entidades al resultado final
entidades = extractor.extract_entities(final_result['texto'])

print("\n==============================")
print("Respuesta Inteligente:")
print(generar_respuesta(entidades))
print("==============================")
