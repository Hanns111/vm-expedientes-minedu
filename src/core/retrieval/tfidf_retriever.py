#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TF-IDF Retriever for document search.

This module provides TF-IDF-based document retrieval functionality
for the MINEDU document search system.
"""

import pickle
import time
import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from src.core.config.security_config import SecurityConfig


class TFIDFRetriever:
    """
    TF-IDF-based document retriever.
    
    This class implements TF-IDF (Term Frequency-Inverse Document Frequency)
    algorithm for document retrieval, providing term-based search capabilities.
    
    Attributes:
        vectorstore_path (str): Path to the TF-IDF vectorstore file
        chunks (List[Dict]): Document chunks for retrieval
        tfidf_vectorizer (TfidfVectorizer): TF-IDF vectorizer instance
        tfidf_matrix: TF-IDF matrix of document vectors
        logger (logging.Logger): Logger instance for debugging
    """
    
    def __init__(self, vectorstore_path: str):
        """
        Initialize the TF-IDF retriever.
        
        Args:
            vectorstore_path (str): Path to the TF-IDF vectorstore pickle file
            
        Raises:
            FileNotFoundError: If the vectorstore file doesn't exist
            ValueError: If the vectorstore is corrupted or invalid
        """
        self.vectorstore_path = Path(vectorstore_path)
        self.chunks: List[Dict[str, Any]] = []
        self.tfidf_vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.logger = self._setup_logging()
        
        if not self.vectorstore_path.exists():
            raise FileNotFoundError(f"Vectorstore not found: {vectorstore_path}")
        
        self._load_vectorstore()
    
    def _setup_logging(self) -> logging.Logger:
        """
        Set up logging configuration for the retriever.
        
        Returns:
            logging.Logger: Configured logger instance
        """
        logger = logging.getLogger('TFIDFRetriever')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _load_vectorstore(self) -> None:
        """
        Load the TF-IDF vectorstore from disk.
        
        Raises:
            ValueError: If the vectorstore is corrupted or missing required components
        """
        try:
            with open(self.vectorstore_path, 'rb') as f:
                vectorstore = pickle.load(f)
            
            self.chunks = vectorstore.get('chunks', [])
            
            if not self.chunks:
                raise ValueError("No chunks found in vectorstore")
            
            # Prepare texts for TF-IDF
            texts = []
            for chunk in self.chunks:
                if isinstance(chunk, dict):
                    text = chunk.get('texto', chunk.get('text', ''))
                else:
                    text = str(chunk)
                texts.append(text)
            
            # Initialize TF-IDF vectorizer
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=10000,
                stop_words=None,  # Keep Spanish stop words for now
                ngram_range=(1, 2),  # Use unigrams and bigrams
                min_df=1,
                max_df=0.95
            )
            
            # Fit and transform the texts
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            
            self.logger.info(f"TF-IDF vectorstore loaded with {len(self.chunks)} chunks")
            self.logger.info(f"TF-IDF matrix shape: {self.tfidf_matrix.shape}")
            
        except Exception as e:
            self.logger.error(f"Error loading vectorstore: {e}")
            raise ValueError(f"Failed to load vectorstore: {e}")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform TF-IDF search on the document collection.
        
        Args:
            query (str): Search query string
            top_k (int): Number of top results to return
            
        Returns:
            List[Dict[str, Any]]: List of search results with scores and metadata
            
        Example:
            >>> retriever = TFIDFRetriever("path/to/vectorstore.pkl")
            >>> results = retriever.search("viáticos nacionales", top_k=3)
            >>> for result in results:
            ...     print(f"Score: {result['score']}, Text: {result['texto'][:100]}...")
        """
        if not self.tfidf_vectorizer or self.tfidf_matrix is None:
            self.logger.warning("TF-IDF model not available")
            return []
        
        try:
            self.logger.info(f"Performing TF-IDF search for: '{query}'")
            start_time = time.time()
            
            # Preprocess query
            processed_query = self._preprocess_text(query)
            self.logger.debug(f"Preprocessed query: {processed_query}")
            
            # Transform query to TF-IDF vector
            query_vector = self.tfidf_vectorizer.transform([processed_query])
            
            # Calculate cosine similarity
            similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
            
            # Get top-k indices
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            # Format results
            results = []
            for idx in top_indices:
                if similarities[idx] > 0:  # Only include results with positive similarity
                    chunk = self.chunks[idx]
                    
                    result = {
                        'score': float(similarities[idx]),
                        'texto': str(chunk.get('texto', chunk.get('text', ''))),
                        'titulo': str(chunk.get('titulo', chunk.get('title', f'Result {idx+1}'))),
                        'metadatos': chunk.get('metadatos', {}),
                        'source': 'tfidf',
                        'index': int(idx),
                        'method': 'TF-IDF'
                    }
                    results.append(result)
            
            elapsed_time = time.time() - start_time
            self.logger.info(
                f"TF-IDF search completed in {elapsed_time:.4f}s, "
                f"found {len(results)} results"
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in TF-IDF search: {e}")
            return []
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for TF-IDF search.
        
        Args:
            text (str): Input text to preprocess
            
        Returns:
            str: Preprocessed text
            
        This method:
        - Converts text to lowercase
        - Removes special characters while preserving Spanish accents
        - Normalizes whitespace
        - Applies basic text cleaning
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but preserve Spanish accents
        text = re.sub(r'[^a-záéíóúüñ\s]', ' ', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the retriever.
        
        Returns:
            Dict[str, Any]: Statistics including chunk count, matrix shape, and vocabulary size
        """
        vocab_size = len(self.tfidf_vectorizer.vocabulary_) if self.tfidf_vectorizer else 0
        matrix_shape = self.tfidf_matrix.shape if self.tfidf_matrix is not None else (0, 0)
        
        return {
            'chunk_count': len(self.chunks),
            'vectorstore_path': str(self.vectorstore_path),
            'model_type': 'TF-IDF',
            'vocabulary_size': vocab_size,
            'matrix_shape': matrix_shape,
            'has_model': self.tfidf_vectorizer is not None
        }


def create_tfidf_retriever(vectorstore_path: str) -> TFIDFRetriever:
    """
    Factory function to create a TF-IDF retriever.
    
    Args:
        vectorstore_path (str): Path to the TF-IDF vectorstore file
        
    Returns:
        TFIDFRetriever: Configured TF-IDF retriever instance
        
    Example:
        >>> retriever = create_tfidf_retriever("data/vectorstores/tfidf.pkl")
        >>> results = retriever.search("consulta de ejemplo")
    """
    return TFIDFRetriever(vectorstore_path)


if __name__ == "__main__":
    # Ejemplo de uso seguro
    retriever = TFIDFRetriever(str(SecurityConfig.VECTORSTORE_PATH))
    print("TFIDFRetriever inicializado con vectorstore seguro.")
    
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python tfidf_retriever.py <vectorstore_path> [query]")
        sys.exit(1)
    
    vectorstore_path = sys.argv[1]
    query = sys.argv[2] if len(sys.argv) > 2 else "¿Cuál es el monto máximo para viáticos?"
    
    try:
        retriever = TFIDFRetriever(vectorstore_path)
        results = retriever.search(query, top_k=3)
        
        print(f"\n🔍 TF-IDF Search Results for: '{query}'")
        print(f"Found {len(results)} results:\n")
        
        for i, result in enumerate(results, 1):
            print(f"{i}. Score: {result['score']:.4f}")
            print(f"   Title: {result['titulo']}")
            print(f"   Text: {result['texto'][:150]}...")
            print()
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 