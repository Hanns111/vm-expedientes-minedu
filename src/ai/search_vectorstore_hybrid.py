import pickle
import re
import os
import logging
from typing import Dict, List, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from entities_extractor import EntitiesExtractor

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/search_hybrid.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("HybridSearch")

# Asegurar que existe el directorio de logs
os.makedirs("logs", exist_ok=True)

class SearchVectorstore:
    """Clase para búsqueda en vectorstore usando TF-IDF y embeddings semánticos."""
    
    def __init__(self, vectorstore_path: str):
        """
        Inicializa el buscador de vectorstore.
        
        Args:
            vectorstore_path: Ruta al vectorstore
        """
        self.vectorstore_path = vectorstore_path
        self.chunks = []
        self.embeddings = None
        self.nn_model = None
        self.embedding_model = None
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.entities_extractor = EntitiesExtractor()
        
        self._load_vectorstore()
    
    def _load_vectorstore(self):
        """
        Carga el vectorstore desde el archivo.
        """
        try:
            logger.info(f"Cargando vectorstore desde {self.vectorstore_path}")
            with open(self.vectorstore_path, 'rb') as f:
                vectorstore = pickle.load(f)
            
            self.chunks = vectorstore['chunks']
            self.embeddings = vectorstore['embeddings']
            self.nn_model = vectorstore['nn_model']
            self.embedding_model = vectorstore['embedding_model']
            
            # Preparar textos para TF-IDF
            texts = [chunk['texto'] if isinstance(chunk, dict) and 'texto' in chunk 
                    else chunk.get('text', "") if isinstance(chunk, dict) 
                    else chunk for chunk in self.chunks]
            
            self.tfidf_vectorizer = TfidfVectorizer()
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            
            logger.info(f"Vectorstore cargado con {len(self.chunks)} chunks")
        except Exception as e:
            logger.error(f"Error al cargar vectorstore: {str(e)}")
            raise
    
    def search(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Realiza una búsqueda híbrida (semántica + TF-IDF).
        
        Args:
            query: Consulta a buscar
            top_k: Número de resultados a devolver
            
        Returns:
            Diccionario con resultados y metadatos
        """
        try:
            # Búsqueda semántica
            query_embedding = self.embedding_model.transform([query])
            _, sem_indices = self.nn_model.kneighbors(query_embedding, n_neighbors=top_k)
            sem_results = [self.chunks[i] for i in sem_indices[0]]
            
            # Filtrar resultados relevantes
            relevant_results = [r for r in sem_results if self._es_relevante(r.get('texto', r.get('text', '')), query)]
            
            if relevant_results:
                final_result = relevant_results[0]
            else:
                final_result = sem_results[0] if sem_results else None
            
            # Extraer entidades
            if final_result:
                entidades = self.entities_extractor.extract_entities(final_result.get('texto', final_result.get('text', '')))
                respuesta = generar_respuesta(entidades)
            else:
                entidades = {}
                respuesta = "No se encontraron resultados relevantes."
            
            # Formatear resultados para ser compatibles con BM25Search
            results = []
            for i, result in enumerate(sem_results[:top_k]):
                result_copy = result.copy()
                result_copy["score"] = 1.0 - (i * 0.1)  # Simular un score
                results.append(result_copy)
            
            return {
                "query": query,
                "results": results,
                "entities": entidades,
                "response": respuesta
            }
        except Exception as e:
            logger.error(f"Error en búsqueda: {str(e)}")
            return {
                "query": query,
                "results": [],
                "entities": {},
                "response": f"Error: {str(e)}"
            }
    
    def _es_relevante(self, texto: str, query: str) -> bool:
        """
        Determina si un texto es relevante para la consulta.
        
        Args:
            texto: Texto a evaluar
            query: Consulta original
            
        Returns:
            True si es relevante, False en caso contrario
        """
        texto_lower = texto.lower()
        query_lower = query.lower()
        
        # Palabras clave específicas para la consulta
        palabras_clave = query_lower.split()
        
        # Verificar si el texto contiene palabras clave de la consulta
        return any(palabra in texto_lower for palabra in palabras_clave)

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
        entidades_rel = []
        for e in entidades["entidades"]:
            # Manejar tanto strings como diccionarios
            if isinstance(e, dict):
                valor = e.get("valor", "")
                if isinstance(valor, str) and ("directiva" in valor.lower() or "normativa" in valor.lower()):
                    entidades_rel.append(valor)
            elif isinstance(e, str) and ("directiva" in e.lower() or "normativa" in e.lower()):
                entidades_rel.append(e)
                
        if entidades_rel:
            respuesta.append("\nReferencias a la normativa:")
            for entidad in entidades_rel:
                respuesta.append(f"- {entidad}")
    
    return "\n".join(respuesta) if respuesta else "No se encontraron datos clave en el texto."

# Código de ejemplo para ejecutar directamente el script
if __name__ == "__main__":
    import sys
    
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("Uso: python search_vectorstore_hybrid.py 'consulta de ejemplo'")
        sys.exit(1)
    
    # Obtener consulta de argumentos
    query = sys.argv[1]
    
    # Crear instancia de búsqueda
    search = SearchVectorstore('data/processed/vectorstore_semantic_full_v2.pkl')
    
    # Realizar búsqueda
    results = search.search(query, top_k=5)
    
    # Mostrar resultados
    print(f"\nConsulta: {query}")
    print(f"Total de resultados: {len(results['results'])}\n")
    
    print("Resultados principales:")
    for i, result in enumerate(results['results'][:3], 1):
        print(f"{i}. Score: {result['score']:.4f}")
        text = result.get('texto', result.get('text', ''))[:150]
        print(f"   {text}...\n")
    
    print("Respuesta Inteligente:")
    print(results['response'])
    print("==============================")

# Fin del archivo
