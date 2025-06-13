#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hybrid Search System for MINEDU Document Search.

This module provides a hybrid search system that combines multiple retrieval
methods (BM25, TF-IDF, and Transformers) for optimal document search results.
"""

import time
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..retrieval.bm25_retriever import BM25Retriever
from ..retrieval.tfidf_retriever import TFIDFRetriever
from ..retrieval.transformer_retriever import TransformerRetriever


class HybridSearch:
    """
    Hybrid search system combining multiple retrieval methods.
    
    This class implements a hybrid search approach that combines:
    - BM25: Fast lexical search
    - TF-IDF: Term frequency-based search
    - Transformers: Semantic search
    
    The system can use different fusion strategies to combine results
    from multiple retrieval methods.
    
    Attributes:
        bm25_retriever (BM25Retriever): BM25-based retriever
        tfidf_retriever (TFIDFRetriever): TF-IDF-based retriever
        transformer_retriever (TransformerRetriever): Transformer-based retriever
        logger (logging.Logger): Logger instance for debugging
    """
    
    def __init__(
        self,
        bm25_vectorstore_path: str,
        tfidf_vectorstore_path: str,
        transformer_vectorstore_path: str,
        fusion_strategy: str = 'weighted'
    ):
        """
        Initialize the hybrid search system.
        
        Args:
            bm25_vectorstore_path (str): Path to BM25 vectorstore
            tfidf_vectorstore_path (str): Path to TF-IDF vectorstore
            transformer_vectorstore_path (str): Path to transformer vectorstore
            fusion_strategy (str): Strategy for combining results ('weighted', 'rank_fusion', 'simple')
            
        Raises:
            FileNotFoundError: If any vectorstore file doesn't exist
            ValueError: If fusion strategy is invalid
        """
        self.fusion_strategy = fusion_strategy
        self.logger = self._setup_logging()
        
        # Validate fusion strategy
        valid_strategies = ['weighted', 'rank_fusion', 'simple']
        if fusion_strategy not in valid_strategies:
            raise ValueError(f"Invalid fusion strategy. Must be one of: {valid_strategies}")
        
        # Initialize retrievers
        self.logger.info("Initializing hybrid search system...")
        
        try:
            self.bm25_retriever = BM25Retriever(bm25_vectorstore_path)
            self.logger.info("BM25 retriever initialized successfully")
        except Exception as e:
            self.logger.warning(f"Failed to initialize BM25 retriever: {e}")
            self.bm25_retriever = None
        
        try:
            self.tfidf_retriever = TFIDFRetriever(tfidf_vectorstore_path)
            self.logger.info("TF-IDF retriever initialized successfully")
        except Exception as e:
            self.logger.warning(f"Failed to initialize TF-IDF retriever: {e}")
            self.tfidf_retriever = None
        
        try:
            self.transformer_retriever = TransformerRetriever(transformer_vectorstore_path)
            self.logger.info("Transformer retriever initialized successfully")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Transformer retriever: {e}")
            self.transformer_retriever = None
        
        # Check if at least one retriever is available
        available_retrievers = sum([
            self.bm25_retriever is not None,
            self.tfidf_retriever is not None,
            self.transformer_retriever is not None
        ])
        
        if available_retrievers == 0:
            raise ValueError("No retrievers could be initialized")
        
        self.logger.info(f"Hybrid search system initialized with {available_retrievers} retrievers")
    
    def _setup_logging(self) -> logging.Logger:
        """
        Set up logging configuration for the hybrid system.
        
        Returns:
            logging.Logger: Configured logger instance
        """
        logger = logging.getLogger('HybridSearch')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        use_methods: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search using multiple retrieval methods.
        
        Args:
            query (str): Search query string
            top_k (int): Number of top results to return
            use_methods (Optional[List[str]]): List of methods to use ('bm25', 'tfidf', 'transformer')
            
        Returns:
            List[Dict[str, Any]]: Combined search results with scores and metadata
            
        Example:
            >>> searcher = HybridSearch(bm25_path, tfidf_path, transformer_path)
            >>> results = searcher.search("viáticos nacionales", top_k=3)
            >>> for result in results:
            ...     print(f"Score: {result['score']}, Method: {result['method']}")
        """
        self.logger.info(f"Performing hybrid search for: '{query}'")
        start_time = time.time()
        
        # Determine which methods to use
        if use_methods is None:
            use_methods = ['bm25', 'tfidf', 'transformer']
        
        # Collect results from each method
        all_results = []
        
        if 'bm25' in use_methods and self.bm25_retriever:
            try:
                bm25_results = self.bm25_retriever.search(query, top_k=top_k)
                all_results.extend(bm25_results)
                self.logger.info(f"BM25 returned {len(bm25_results)} results")
            except Exception as e:
                self.logger.error(f"Error in BM25 search: {e}")
        
        if 'tfidf' in use_methods and self.tfidf_retriever:
            try:
                tfidf_results = self.tfidf_retriever.search(query, top_k=top_k)
                all_results.extend(tfidf_results)
                self.logger.info(f"TF-IDF returned {len(tfidf_results)} results")
            except Exception as e:
                self.logger.error(f"Error in TF-IDF search: {e}")
        
        if 'transformer' in use_methods and self.transformer_retriever:
            try:
                transformer_results = self.transformer_retriever.search(query, top_k=top_k)
                all_results.extend(transformer_results)
                self.logger.info(f"Transformer returned {len(transformer_results)} results")
            except Exception as e:
                self.logger.error(f"Error in Transformer search: {e}")
        
        # Combine results using the specified fusion strategy
        if self.fusion_strategy == 'weighted':
            final_results = self._weighted_fusion(all_results, top_k)
        elif self.fusion_strategy == 'rank_fusion':
            final_results = self._rank_fusion(all_results, top_k)
        else:  # simple
            final_results = self._simple_fusion(all_results, top_k)
        
        elapsed_time = time.time() - start_time
        self.logger.info(
            f"Hybrid search completed in {elapsed_time:.4f}s, "
            f"returning {len(final_results)} results"
        )
        
        return final_results
    
    def _weighted_fusion(self, results: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """
        Combine results using weighted fusion strategy.
        
        Args:
            results (List[Dict[str, Any]]): Results from all methods
            top_k (int): Number of top results to return
            
        Returns:
            List[Dict[str, Any]]: Combined results with weighted scores
        """
        # Group results by document index
        doc_scores = {}
        
        for result in results:
            doc_id = result.get('index', result.get('texto', ''))
            
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {
                    'doc': result,
                    'scores': [],
                    'methods': []
                }
            
            doc_scores[doc_id]['scores'].append(result['score'])
            doc_scores[doc_id]['methods'].append(result['method'])
        
        # Calculate weighted scores
        final_results = []
        for doc_id, data in doc_scores.items():
            # Weight by method (can be customized)
            weights = {
                'BM25': 0.3,
                'TF-IDF': 0.3,
                'Transformer': 0.4
            }
            
            weighted_score = 0
            total_weight = 0
            
            for score, method in zip(data['scores'], data['methods']):
                weight = weights.get(method, 0.33)
                weighted_score += score * weight
                total_weight += weight
            
            if total_weight > 0:
                final_score = weighted_score / total_weight
            else:
                final_score = max(data['scores'])
            
            # Create final result
            final_result = data['doc'].copy()
            final_result['score'] = final_score
            final_result['hybrid_score'] = final_score
            final_result['methods_used'] = data['methods']
            final_result['source'] = 'hybrid'
            
            final_results.append(final_result)
        
        # Sort by final score and return top_k
        final_results.sort(key=lambda x: x['score'], reverse=True)
        return final_results[:top_k]
    
    def _rank_fusion(self, results: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """
        Combine results using rank fusion strategy.
        
        Args:
            results (List[Dict[str, Any]]): Results from all methods
            top_k (int): Number of top results to return
            
        Returns:
            List[Dict[str, Any]]: Combined results using rank fusion
        """
        # Group results by document index
        doc_ranks = {}
        
        for result in results:
            doc_id = result.get('index', result.get('texto', ''))
            
            if doc_id not in doc_ranks:
                doc_ranks[doc_id] = {
                    'doc': result,
                    'ranks': [],
                    'methods': []
                }
            
            # Calculate rank (inverse of position in results)
            doc_ranks[doc_id]['ranks'].append(1.0 / (len(doc_ranks[doc_id]['ranks']) + 1))
            doc_ranks[doc_id]['methods'].append(result['method'])
        
        # Calculate combined rank scores
        final_results = []
        for doc_id, data in doc_ranks.items():
            combined_rank = sum(data['ranks'])
            
            final_result = data['doc'].copy()
            final_result['score'] = combined_rank
            final_result['hybrid_score'] = combined_rank
            final_result['methods_used'] = data['methods']
            final_result['source'] = 'hybrid'
            
            final_results.append(final_result)
        
        # Sort by combined rank and return top_k
        final_results.sort(key=lambda x: x['score'], reverse=True)
        return final_results[:top_k]
    
    def _simple_fusion(self, results: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """
        Combine results using simple fusion strategy (deduplication).
        
        Args:
            results (List[Dict[str, Any]]): Results from all methods
            top_k (int): Number of top results to return
            
        Returns:
            List[Dict[str, Any]]: Combined results with deduplication
        """
        # Remove duplicates based on document index
        seen_docs = set()
        unique_results = []
        
        for result in results:
            doc_id = result.get('index', result.get('texto', ''))
            
            if doc_id not in seen_docs:
                seen_docs.add(doc_id)
                unique_results.append(result)
        
        # Sort by score and return top_k
        unique_results.sort(key=lambda x: x['score'], reverse=True)
        return unique_results[:top_k]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the hybrid search system.
        
        Returns:
            Dict[str, Any]: Statistics including available methods and fusion strategy
        """
        return {
            'fusion_strategy': self.fusion_strategy,
            'available_methods': {
                'bm25': self.bm25_retriever is not None,
                'tfidf': self.tfidf_retriever is not None,
                'transformer': self.transformer_retriever is not None
            },
            'total_methods': sum([
                self.bm25_retriever is not None,
                self.tfidf_retriever is not None,
                self.transformer_retriever is not None
            ])
        }


def create_hybrid_search(
    bm25_vectorstore_path: str,
    tfidf_vectorstore_path: str,
    transformer_vectorstore_path: str,
    fusion_strategy: str = 'weighted'
) -> HybridSearch:
    """
    Factory function to create a hybrid search system.
    
    Args:
        bm25_vectorstore_path (str): Path to BM25 vectorstore
        tfidf_vectorstore_path (str): Path to TF-IDF vectorstore
        transformer_vectorstore_path (str): Path to transformer vectorstore
        fusion_strategy (str): Strategy for combining results
        
    Returns:
        HybridSearch: Configured hybrid search system
        
    Example:
        >>> searcher = create_hybrid_search(bm25_path, tfidf_path, transformer_path)
        >>> results = searcher.search("consulta de ejemplo")
    """
    return HybridSearch(
        bm25_vectorstore_path,
        tfidf_vectorstore_path,
        transformer_vectorstore_path,
        fusion_strategy
    )


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python hybrid_search.py <bm25_path> <tfidf_path> <transformer_path> [query]")
        sys.exit(1)
    
    bm25_path = sys.argv[1]
    tfidf_path = sys.argv[2]
    transformer_path = sys.argv[3]
    query = sys.argv[4] if len(sys.argv) > 4 else "¿Cuál es el monto máximo para viáticos?"
    
    try:
        searcher = HybridSearch(bm25_path, tfidf_path, transformer_path)
        results = searcher.search(query, top_k=3)
        
        print(f"\n🔍 Hybrid Search Results for: '{query}'")
        print(f"Found {len(results)} results:\n")
        
        for i, result in enumerate(results, 1):
            print(f"{i}. Score: {result['score']:.4f}")
            print(f"   Methods: {result.get('methods_used', [result['method']])}")
            print(f"   Text: {result['texto'][:150]}...")
            print()
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 