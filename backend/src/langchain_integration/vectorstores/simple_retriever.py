"""
Retriever simple que usa los chunks existentes
Implementación que funciona SIN dependencias de LangChain hasta que se instalen
"""
import json
import logging
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import math

logger = logging.getLogger(__name__)

@dataclass
class Document:
    """Documento simple compatible con LangChain"""
    page_content: str
    metadata: Dict[str, Any]
    
    def __init__(self, page_content: str, metadata: Dict[str, Any] = None):
        self.page_content = page_content
        self.metadata = metadata or {}

class SimpleRetriever:
    """Retriever simple usando chunks existentes sin LangChain"""
    
    def __init__(self, chunks_path: str = None):
        if chunks_path is None:
            # Path absoluto basado en el directorio del proyecto
            current_file = Path(__file__)
            # backend/src/langchain_integration/vectorstores/simple_retriever.py
            # Subir 4 niveles: vectorstores -> langchain_integration -> src -> backend -> root
            project_root = current_file.parent.parent.parent.parent.parent 
            self.chunks_path = project_root / "data" / "processed" / "chunks.json"
        else:
            self.chunks_path = chunks_path
        self.documents = []
        self.load_chunks()
    
    def load_chunks(self):
        """Cargar chunks existentes"""
        try:
            chunks_file = Path(self.chunks_path)
            if not chunks_file.exists():
                logger.error(f"Archivo de chunks no encontrado: {self.chunks_path}")
                return
            
            with open(chunks_file, 'r', encoding='utf-8') as f:
                chunks_data = json.load(f)
            
            self.documents = []
            for chunk in chunks_data:
                doc = Document(
                    page_content=chunk.get('texto', ''),
                    metadata={
                        'id': chunk.get('id', ''),
                        'titulo': chunk.get('titulo', ''),
                        'source': chunk.get('metadatos', {}).get('source', ''),
                        'page': chunk.get('metadatos', {}).get('page', 0),
                        'type': chunk.get('metadatos', {}).get('type', ''),
                        'section': chunk.get('metadatos', {}).get('section', ''),
                        'original_chunk': chunk
                    }
                )
                self.documents.append(doc)
            
            logger.info(f"Cargados {len(self.documents)} documentos desde {self.chunks_path}")
            
        except Exception as e:
            logger.error(f"Error cargando chunks: {e}")
            self.documents = []
    
    def simple_similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Búsqueda por similitud simple usando coincidencias de texto"""
        if not self.documents:
            return []
        
        query_words = self._normalize_text(query).split()
        scored_docs = []
        
        for doc in self.documents:
            score = self._calculate_similarity(query_words, doc.page_content)
            if score > 0:
                scored_docs.append((doc, score))
        
        # Ordenar por score descendente
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # Retornar top k documentos
        return [doc for doc, score in scored_docs[:k]]
    
    def _normalize_text(self, text: str) -> str:
        """Normalizar texto para búsqueda"""
        # Convertir a minúsculas
        text = text.lower()
        
        # Normalizar acentos y caracteres especiales
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'ü': 'u'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Remover caracteres especiales excepto espacios
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Normalizar espacios
        text = ' '.join(text.split())
        
        return text
    
    def _calculate_similarity(self, query_words: List[str], document_text: str) -> float:
        """Calcular similitud simple entre query y documento"""
        doc_text = self._normalize_text(document_text)
        doc_words = doc_text.split()
        
        if not doc_words:
            return 0.0
        
        # Contar coincidencias exactas
        exact_matches = sum(1 for word in query_words if word in doc_words)
        
        # Contar coincidencias parciales (substring)
        partial_matches = 0
        for query_word in query_words:
            if len(query_word) > 3:  # Solo palabras largas
                for doc_word in doc_words:
                    if query_word in doc_word or doc_word in query_word:
                        partial_matches += 0.5
                        break
        
        # Bonus por coincidencias de frases
        phrase_bonus = 0
        if len(query_words) > 1:
            query_bigrams = [f"{query_words[i]} {query_words[i+1]}" 
                           for i in range(len(query_words)-1)]
            for bigram in query_bigrams:
                if bigram in doc_text:
                    phrase_bonus += 2
        
        # Calcular score final
        total_score = exact_matches * 2 + partial_matches + phrase_bonus
        
        # Normalizar por longitud del documento (penalizar documentos muy largos)
        normalized_score = total_score / math.log(len(doc_words) + 1)
        
        return normalized_score
    
    def search_by_keywords(self, keywords: List[str], k: int = 5) -> List[Document]:
        """Búsqueda específica por palabras clave"""
        if not self.documents:
            return []
        
        scored_docs = []
        normalized_keywords = [self._normalize_text(kw) for kw in keywords]
        
        for doc in self.documents:
            doc_text = self._normalize_text(doc.page_content)
            score = 0
            
            for keyword in normalized_keywords:
                # Contar ocurrencias de cada keyword
                count = doc_text.count(keyword)
                score += count * len(keyword)  # Palabras más largas valen más
            
            if score > 0:
                scored_docs.append((doc, score))
        
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in scored_docs[:k]]
    
    def get_documents_by_metadata(self, metadata_filter: Dict[str, Any]) -> List[Document]:
        """Filtrar documentos por metadatos"""
        filtered_docs = []
        
        for doc in self.documents:
            match = True
            for key, value in metadata_filter.items():
                if key not in doc.metadata or doc.metadata[key] != value:
                    match = False
                    break
            
            if match:
                filtered_docs.append(doc)
        
        return filtered_docs
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del retriever"""
        if not self.documents:
            return {"total_documents": 0}
        
        # Estadísticas básicas
        total_docs = len(self.documents)
        total_chars = sum(len(doc.page_content) for doc in self.documents)
        avg_length = total_chars / total_docs if total_docs > 0 else 0
        
        # Tipos de documentos
        doc_types = {}
        sources = set()
        
        for doc in self.documents:
            doc_type = doc.metadata.get('type', 'unknown')
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            source = doc.metadata.get('source', '')
            if source:
                sources.add(source)
        
        return {
            "total_documents": total_docs,
            "total_characters": total_chars,
            "average_length": round(avg_length, 2),
            "document_types": doc_types,
            "unique_sources": len(sources),
            "chunks_loaded": True
        }

# Instancia global
retriever = SimpleRetriever()