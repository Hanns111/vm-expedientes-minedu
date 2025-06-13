#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BM25 Retriever for document search.

This module provides BM25-based document retrieval functionality
for the MINEDU document search system.
"""

import pickle
import time
import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from rank_bm25 import BM25Okapi


class BM25Retriever:
    """
    BM25-based document retriever.
    
    This class implements BM25 (Best Matching 25) algorithm for document
    retrieval, providing fast lexical search capabilities.
    
    Attributes:
        vectorstore_path (str): Path to the BM25 vectorstore file
        bm25 (BM25Okapi): BM25 model instance
        chunks (List[Dict]): Document chunks for retrieval
        logger (logging.Logger): Logger instance for debugging
    """
    
    def __init__(self, vectorstore_path: str):
        """
        Initialize the BM25 retriever.
        
        Args:
            vectorstore_path (str): Path to the BM25 vectorstore pickle file
            
        Raises:
            FileNotFoundError: If the vectorstore file doesn't exist
            ValueError: If the vectorstore is corrupted or invalid
        """
        self.vectorstore_path = Path(vectorstore_path)
        self.bm25: Optional[BM25Okapi] = None
        self.chunks: List[Dict[str, Any]] = []
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
        logger = logging.getLogger('BM25Retriever')
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
        Load the BM25 vectorstore from disk.
        
        Raises:
            ValueError: If the vectorstore is corrupted or missing required components
        """
        try:
            with open(self.vectorstore_path, 'rb') as f:
                vectorstore = pickle.load(f)
            
            self.bm25 = vectorstore.get('bm25_index')
            self.chunks = vectorstore.get('chunks', [])
            
            if not self.bm25:
                raise ValueError("BM25 model not found in vectorstore")
            
            if not self.chunks:
                raise ValueError("No chunks found in vectorstore")
            
            self.logger.info(f"BM25 vectorstore loaded with {len(self.chunks)} chunks")
            
        except Exception as e:
            self.logger.error(f"Error loading vectorstore: {e}")
            raise ValueError(f"Failed to load vectorstore: {e}")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform BM25 search on the document collection.
        
        Args:
            query (str): Search query string
            top_k (int): Number of top results to return
            
        Returns:
            List[Dict[str, Any]]: List of search results with scores and metadata
            
        Example:
            >>> retriever = BM25Retriever("path/to/vectorstore.pkl")
            >>> results = retriever.search("viáticos nacionales", top_k=3)
            >>> for result in results:
            ...     print(f"Score: {result['score']}, Text: {result['texto'][:100]}...")
        """
        if not self.bm25 or not self.chunks:
            self.logger.warning("BM25 model or chunks not available")
            return []
        
        try:
            self.logger.info(f"Performing BM25 search for: '{query}'")
            start_time = time.time()
            
            # Preprocess query
            query_tokens = self._preprocess_text(query).split()
            self.logger.debug(f"Preprocessed query tokens: {query_tokens}")
            
            # Get BM25 scores
            scores = self.bm25.get_scores(query_tokens)
            
            # Get top-k indices
            top_indices = sorted(
                range(len(scores)), 
                key=lambda i: scores[i], 
                reverse=True
            )[:top_k]
            
            # Format results
            results = []
            for idx in top_indices:
                if scores[idx] > 0:  # Only include results with positive scores
                    chunk = self.chunks[idx]
                    
                    result = {
                        'score': float(scores[idx]),
                        'texto': str(chunk.get('texto', chunk.get('text', ''))),
                        'titulo': str(chunk.get('titulo', chunk.get('title', f'Result {idx+1}'))),
                        'metadatos': chunk.get('metadatos', {}),
                        'source': 'bm25',
                        'index': idx,
                        'method': 'BM25'
                    }
                    results.append(result)
            
            elapsed_time = time.time() - start_time
            self.logger.info(
                f"BM25 search completed in {elapsed_time:.4f}s, "
                f"found {len(results)} results"
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in BM25 search: {e}")
            return []
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for BM25 search.
        
        Args:
            text (str): Input text to preprocess
            
        Returns:
            str: Preprocessed text
            
        This method:
        - Converts text to lowercase
        - Removes special characters while preserving Spanish accents
        - Normalizes whitespace
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
            Dict[str, Any]: Statistics including chunk count and model info
        """
        return {
            'chunk_count': len(self.chunks),
            'vectorstore_path': str(self.vectorstore_path),
            'model_type': 'BM25Okapi',
            'has_model': self.bm25 is not None
        }


def create_bm25_retriever(vectorstore_path: str) -> BM25Retriever:
    """
    Factory function to create a BM25 retriever.
    
    Args:
        vectorstore_path (str): Path to the BM25 vectorstore file
        
    Returns:
        BM25Retriever: Configured BM25 retriever instance
        
    Example:
        >>> retriever = create_bm25_retriever("data/vectorstores/bm25.pkl")
        >>> results = retriever.search("consulta de ejemplo")
    """
    return BM25Retriever(vectorstore_path)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python bm25_retriever.py <vectorstore_path> [query]")
        sys.exit(1)
    
    vectorstore_path = sys.argv[1]
    query = sys.argv[2] if len(sys.argv) > 2 else "¿Cuál es el monto máximo para viáticos?"
    
    try:
        retriever = BM25Retriever(vectorstore_path)
        results = retriever.search(query, top_k=3)
        
        print(f"\n🔍 BM25 Search Results for: '{query}'")
        print(f"Found {len(results)} results:\n")
        
        for i, result in enumerate(results, 1):
            print(f"{i}. Score: {result['score']:.4f}")
            print(f"   Title: {result['titulo']}")
            print(f"   Text: {result['texto'][:150]}...")
            print()
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 