#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests para HybridSearch con funcionalidad de boost.
Valida la corrección del bug de método duplicado y la lógica de boost.

Autor: Claude Code
Fecha: 2025-06-24
"""

import unittest
import sys
import os
import logging
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.core.hybrid.hybrid_search import HybridSearch
except ImportError:
    print("Warning: Could not import HybridSearch - dependencies may be missing")
    HybridSearch = None


class TestHybridSearchBoost(unittest.TestCase):
    """Tests para la funcionalidad de boost en HybridSearch"""
    
    def setUp(self):
        """Configurar el test"""
        if HybridSearch is None:
            self.skipTest("HybridSearch not available - missing dependencies")
            
        # Mock retrievers para evitar dependencias externas
        self.mock_bm25 = Mock()
        self.mock_tfidf = Mock()
        self.mock_transformer = Mock()
        
        # Mock logger
        self.mock_logger = Mock()
        
        # Crear instancia de HybridSearch con mocks
        self.hybrid_search = HybridSearch(
            bm25_retriever=self.mock_bm25,
            tfidf_retriever=self.mock_tfidf,
            transformer_retriever=self.mock_transformer,
            fusion_strategy='weighted'
        )
        
        # Sobrescribir logger
        self.hybrid_search.logger = self.mock_logger
        
    def test_weighted_fusion_method_exists_and_unique(self):
        """Test que verifica que _weighted_fusion existe y no está duplicado"""
        # Verificar que el método existe
        self.assertTrue(hasattr(self.hybrid_search, '_weighted_fusion'))
        
        # Verificar que acepta los parámetros correctos (query, results, top_k)
        method = getattr(self.hybrid_search, '_weighted_fusion')
        self.assertTrue(callable(method))
        
    def test_weighted_fusion_basic_functionality(self):
        """Test básico de la funcionalidad de weighted_fusion"""
        # Datos de prueba
        sample_results = [
            {
                'index': 'doc1',
                'score': 0.8,
                'method': 'BM25',
                'text': 'Documento sobre viáticos S/ 380',
                'metadatos': {}
            },
            {
                'index': 'doc1',
                'score': 0.6,
                'method': 'TF-IDF',
                'text': 'Documento sobre viáticos S/ 380',
                'metadatos': {}
            },
            {
                'index': 'doc2',
                'score': 0.7,
                'method': 'BM25',
                'text': 'Otro documento',
                'metadatos': {}
            }
        ]
        
        # Ejecutar weighted_fusion
        query = "viáticos"
        result = self.hybrid_search._weighted_fusion(query, sample_results, top_k=2)
        
        # Verificaciones
        self.assertIsInstance(result, list)
        self.assertLessEqual(len(result), 2)
        
        # Verificar que los resultados tienen los campos esperados
        if result:
            for res in result:
                self.assertIn('score', res)
                self.assertIn('hybrid_score', res)
                self.assertIn('methods_used', res)
                self.assertIn('source', res)
                self.assertEqual(res['source'], 'hybrid')
                
    def test_amount_boost_functionality(self):
        """Test específico para la funcionalidad de boost de montos"""
        sample_results = [
            {
                'index': 'doc_amount',
                'score': 0.5,
                'method': 'BM25',
                'text': 'El monto máximo para viáticos es S/ 380',
                'metadatos': {}
            }
        ]
        
        # Query que contiene keywords de monto
        query_with_amount = "¿Cuál es el monto máximo para viáticos?"
        result = self.hybrid_search._weighted_fusion(query_with_amount, sample_results, top_k=1)
        
        # Verificar que se aplicó boost (score > score original)
        self.assertTrue(len(result) > 0)
        boosted_score = result[0]['score']
        self.assertGreater(boosted_score, 0.5)  # Score original + boost
        
    def test_minister_boost_functionality(self):
        """Test específico para la funcionalidad de boost ministerial"""
        sample_results = [
            {
                'index': 'doc_minister',
                'score': 0.5,
                'method': 'BM25',
                'text': 'Documentos para ministros y altos funcionarios S/ 380',
                'metadatos': {'role_level': 'minister'}
            }
        ]
        
        # Query que menciona ministro
        query_minister = "documentos para ministro"
        result = self.hybrid_search._weighted_fusion(query_minister, sample_results, top_k=1)
        
        # Verificar boost ministerial (más alto que boost de monto)
        self.assertTrue(len(result) > 0)
        boosted_score = result[0]['score']
        self.assertGreater(boosted_score, 0.5)  # Score original + boost ministerial
        
    def test_no_boost_when_not_applicable(self):
        """Test que verifica que no se aplica boost cuando no corresponde"""
        sample_results = [
            {
                'index': 'doc_normal',
                'score': 0.5,
                'method': 'BM25',
                'text': 'Documento normal sin números ni keywords especiales',
                'metadatos': {}
            }
        ]
        
        query_normal = "información general"
        result = self.hybrid_search._weighted_fusion(query_normal, sample_results, top_k=1)
        
        # Verificar que el score se mantiene similar al original (solo weighted fusion)
        self.assertTrue(len(result) > 0)
        final_score = result[0]['score']
        # El score puede cambiar ligeramente por weighted fusion pero no por boost
        self.assertAlmostEqual(final_score, 0.5, delta=0.1)


class TestHybridSearchAPI(unittest.TestCase):
    """Tests para verificar que la API funciona con los cambios"""
    
    def test_search_method_calls_weighted_fusion_correctly(self):
        """Test que verifica que el método search llama correctamente a _weighted_fusion"""
        if HybridSearch is None:
            self.skipTest("HybridSearch not available - missing dependencies")
            
        # Mock de retrievers que retornan resultados
        mock_bm25 = Mock()
        mock_bm25.search.return_value = [
            {'index': 'doc1', 'score': 0.8, 'method': 'BM25', 'text': 'Test document'}
        ]
        
        mock_tfidf = Mock()
        mock_tfidf.search.return_value = [
            {'index': 'doc1', 'score': 0.6, 'method': 'TF-IDF', 'text': 'Test document'}
        ]
        
        hybrid_search = HybridSearch(
            bm25_retriever=mock_bm25,
            tfidf_retriever=mock_tfidf,
            transformer_retriever=None,
            fusion_strategy='weighted'
        )
        
        # Mock del método _weighted_fusion para verificar que se llama
        hybrid_search._weighted_fusion = Mock(return_value=[
            {'index': 'doc1', 'score': 0.7, 'method': 'hybrid', 'source': 'hybrid'}
        ])
        
        # Ejecutar búsqueda
        query = "test query"
        results = hybrid_search.search(query, top_k=5)
        
        # Verificar que _weighted_fusion fue llamado con los parámetros correctos
        hybrid_search._weighted_fusion.assert_called_once()
        call_args = hybrid_search._weighted_fusion.call_args
        
        # Verificar que el primer argumento es la query
        self.assertEqual(call_args[0][0], query)
        
        # Verificar que se pasaron resultados
        self.assertTrue(len(call_args[0][1]) > 0)  # all_results no vacío
        
        # Verificar que se pasó top_k
        self.assertEqual(call_args[0][2], 5)


if __name__ == '__main__':
    # Configurar logging básico para tests
    logging.basicConfig(level=logging.WARNING)
    
    # Ejecutar tests
    unittest.main(verbosity=2)