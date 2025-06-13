#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Transformer Retriever for semantic document search.

This module provides transformer-based document retrieval functionality
for the MINEDU document search system using sentence transformers.
"""

import pickle
import time
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class TransformerRetriever:
    """
    Transformer-based document retriever using sentence transformers.
    
    This class implements semantic search using pre-trained transformer models
    for finding semantically similar documents.
    
    Attributes:
        vectorstore_path (str): Path to the transformer vectorstore file
        model (SentenceTransformer): Sentence transformer model instance
        chunks (List[Dict]): Document chunks for retrieval
        embeddings (np.ndarray): Pre-computed document embeddings
        logger (logging.Logger): Logger instance for debugging
    """
    
    def __init__(
        self, 
        vectorstore_path: str,
        model_name: Optional[str] = None,
        fallback_model: str = 'paraphrase-multilingual-MiniLM-L12-v2',
        device: str = 'cpu'
    ):
        """
        Initialize the transformer retriever.
        
        Args:
            vectorstore_path (str): Path to the transformer vectorstore pickle file
            model_name (Optional[str]): Name of the transformer model to use
            fallback_model (str): Fallback model if the primary model fails
            device (str): Device to run the model on ('cpu' or 'cuda')
            
        Raises:
            FileNotFoundError: If the vectorstore file doesn't exist
            ValueError: If the vectorstore is corrupted or invalid
        """
        self.vectorstore_path = Path(vectorstore_path)
        self.fallback_model = fallback_model
        self.device = device
        self.model: Optional[SentenceTransformer] = None
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        self.logger = self._setup_logging()
        
        if not self.vectorstore_path.exists():
            raise FileNotFoundError(f"Vectorstore not found: {vectorstore_path}")
        
        self._load_vectorstore()
        self._load_model(model_name)
    
    def _setup_logging(self) -> logging.Logger:
        """
        Set up logging configuration for the retriever.
        
        Returns:
            logging.Logger: Configured logger instance
        """
        logger = logging.getLogger('TransformerRetriever')
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
        Load the transformer vectorstore from disk.
        
        Raises:
            ValueError: If the vectorstore is corrupted or missing required components
        """
        try:
            self.logger.info(f"Loading vectorstore from {self.vectorstore_path}")
            start_time = time.time()
            
            with open(self.vectorstore_path, 'rb') as f:
                vectorstore = pickle.load(f)
            
            # Verify vectorstore structure
            required_keys = ['chunks', 'embeddings', 'model_name']
            for key in required_keys:
                if key not in vectorstore:
                    raise ValueError(f"Invalid vectorstore: missing key '{key}'")
            
            self.chunks = vectorstore['chunks']
            self.embeddings = vectorstore['embeddings']
            
            self.logger.info(f"Vectorstore loaded in {time.time() - start_time:.2f} seconds")
            self.logger.info(f"Vectorstore loaded with {len(self.chunks)} chunks")
            self.logger.info(f"Model used for embeddings: {vectorstore['model_name']}")
            
        except Exception as e:
            self.logger.error(f"Error loading vectorstore: {e}")
            raise ValueError(f"Failed to load vectorstore: {e}")
    
    def _load_model(self, model_name: Optional[str]) -> None:
        """
        Load the sentence transformer model.
        
        Args:
            model_name (Optional[str]): Name of the model to load
        """
        try:
            # Determine model to use
            if not model_name:
                # Try to get model name from vectorstore metadata
                with open(self.vectorstore_path, 'rb') as f:
                    vectorstore = pickle.load(f)
                model_name = vectorstore.get('model_name', self.fallback_model)
            
            self.logger.info(f"Loading model {model_name}...")
            start_time = time.time()
            
            self.model = SentenceTransformer(model_name, device=self.device)
            
            self.logger.info(f"Model {model_name} loaded in {time.time() - start_time:.2f} seconds")
            
        except Exception as e:
            self.logger.warning(f"Error loading primary model: {e}")
            self.logger.info(f"Trying fallback model {self.fallback_model}...")
            
            try:
                start_time = time.time()
                self.model = SentenceTransformer(self.fallback_model, device=self.device)
                self.logger.info(f"Fallback model {self.fallback_model} loaded in {time.time() - start_time:.2f} seconds")
                self.logger.warning("Using fallback model. Results may vary.")
            except Exception as e2:
                self.logger.error(f"Error loading fallback model: {e2}")
                raise ValueError(f"Could not load any model: {e}, {e2}")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform semantic search on the document collection.
        
        Args:
            query (str): Search query string
            top_k (int): Number of top results to return
            
        Returns:
            List[Dict[str, Any]]: List of search results with scores and metadata
            
        Example:
            >>> retriever = TransformerRetriever("path/to/vectorstore.pkl")
            >>> results = retriever.search("viáticos nacionales", top_k=3)
            >>> for result in results:
            ...     print(f"Score: {result['score']}, Text: {result['texto'][:100]}...")
        """
        if not self.model or self.embeddings is None:
            self.logger.warning("Transformer model or embeddings not available")
            return []
        
        try:
            self.logger.info(f"Performing semantic search for: '{query}'")
            start_time = time.time()
            
            # Generate query embedding
            query_embedding = self.model.encode([query])[0]
            
            # Calculate similarity with all embeddings
            similarities = cosine_similarity([query_embedding], self.embeddings)[0]
            
            # Get top-k indices
            top_indices = similarities.argsort()[-top_k:][::-1]
            
            # Format results
            results = []
            for idx in top_indices:
                chunk = self.chunks[idx]
                score = float(similarities[idx])
                
                # Ensure chunk has 'texto' key
                if 'texto' not in chunk and 'text' in chunk:
                    chunk['texto'] = chunk['text']
                
                result = {
                    'score': score,
                    'texto': str(chunk.get('texto', chunk.get('text', ''))),
                    'titulo': str(chunk.get('titulo', chunk.get('title', f'Result {idx+1}'))),
                    'metadatos': chunk.get('metadatos', {}),
                    'source': 'transformer',
                    'index': int(idx),
                    'method': 'Transformer'
                }
                results.append(result)
            
            elapsed_time = time.time() - start_time
            self.logger.info(
                f"Semantic search completed in {elapsed_time:.4f}s, "
                f"found {len(results)} results"
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in semantic search: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the retriever.
        
        Returns:
            Dict[str, Any]: Statistics including chunk count, embedding shape, and model info
        """
        embedding_shape = self.embeddings.shape if self.embeddings is not None else (0, 0)
        model_name = self.model.get_model_name() if self.model else "None"
        
        return {
            'chunk_count': len(self.chunks),
            'vectorstore_path': str(self.vectorstore_path),
            'model_type': 'SentenceTransformer',
            'model_name': model_name,
            'embedding_shape': embedding_shape,
            'device': self.device,
            'has_model': self.model is not None
        }


def create_transformer_retriever(
    vectorstore_path: str,
    model_name: Optional[str] = None,
    device: str = 'cpu'
) -> TransformerRetriever:
    """
    Factory function to create a transformer retriever.
    
    Args:
        vectorstore_path (str): Path to the transformer vectorstore file
        model_name (Optional[str]): Name of the transformer model to use
        device (str): Device to run the model on
        
    Returns:
        TransformerRetriever: Configured transformer retriever instance
        
    Example:
        >>> retriever = create_transformer_retriever("data/vectorstores/transformers.pkl")
        >>> results = retriever.search("consulta de ejemplo")
    """
    return TransformerRetriever(vectorstore_path, model_name, device=device)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python transformer_retriever.py <vectorstore_path> [query]")
        sys.exit(1)
    
    vectorstore_path = sys.argv[1]
    query = sys.argv[2] if len(sys.argv) > 2 else "¿Cuál es el monto máximo para viáticos?"
    
    try:
        retriever = TransformerRetriever(vectorstore_path)
        results = retriever.search(query, top_k=3)
        
        print(f"\n🔍 Transformer Search Results for: '{query}'")
        print(f"Found {len(results)} results:\n")
        
        for i, result in enumerate(results, 1):
            print(f"{i}. Score: {result['score']:.4f}")
            print(f"   Title: {result['titulo']}")
            print(f"   Text: {result['texto'][:150]}...")
            print()
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 