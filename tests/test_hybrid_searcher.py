#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pruebas unitarias para el HybridSearcher.

Autor: Hanns
Fecha: 2025-06-14
"""

import unittest
import sys
import os
import tempfile
import pickle
from pathlib import Path
from unittest.mock import Mock, patch

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.retrieval.hybrid_fusion import HybridFusion, MockRetriever


class TestHybridFusion(unittest.TestCase):
    """Pruebas para el sistema de fusión híbrida"""
    
    def setUp(self):
        """Configurar el test"""
        # Crear retrievers mock para testing
        self.mock_bm25 = MockRetriever("bm25", [
            {"id": "doc1", "text": "Documento sobre viáticos nacionales", "score": 0.9},
            {"id": "doc2", "text": "Documento sobre autorización de gastos", "score": 0.8},
            {"id": "doc3", "text": "Documento sobre rendición de cuentas", "score": 0.7}
        ])
        
        self.mock_dense = MockRetriever("dense", [
            {"id": "doc2", "text": "Documento sobre autorización de gastos", "score": 0.95},
            {"id": "doc4", "text": "Documento sobre procedimientos administrativos", "score": 0.85},
            {"id": "doc1", "text": "Documento sobre viáticos nacionales", "score": 0.75}
        ])
        
        self.fusion = HybridFusion(
            retrievers={"bm25": self.mock_bm25, "dense": self.mock_dense},
            method="rrf",
            weights={"bm25": 1.0, "dense": 1.0}
        )
    
    def test_initialization(self):
        """Probar inicialización del sistema de fusión"""
        self.assertIsNotNone(self.fusion)
        self.assertEqual(self.fusion.method, "rrf")
        self.assertEqual(self.fusion.rrf_k, 60)
        self.assertTrue(self.fusion.deduplicate)
        self.assertEqual(len(self.fusion.retrievers), 2)
    
    def test_rrf_fusion(self):
        """Probar fusión con Reciprocal Rank Fusion"""
        results = self.fusion.search("viáticos nacionales", top_k=3)
        
        self.assertIsInstance(results, dict)
        self.assertIn("query", results)
        self.assertIn("results", results)
        self.assertIn("time_taken", results)
        self.assertIn("fusion_method", results)
        
        # Verificar que hay resultados
        self.assertGreater(len(results["results"]), 0)
        
        # Verificar formato de resultados
        for result in results["results"]:
            self.assertIn("id", result)
            self.assertIn("text", result)
            self.assertIn("score", result)
            self.assertIn("fusion_sources", result)
            self.assertIn("fusion_method", result)
    
    def test_weighted_fusion(self):
        """Probar fusión ponderada"""
        fusion_weighted = HybridFusion(
            retrievers={"bm25": self.mock_bm25, "dense": self.mock_dense},
            method="weighted",
            weights={"bm25": 0.7, "dense": 0.3}
        )
        
        results = fusion_weighted.search("viáticos nacionales", top_k=3)
        
        self.assertEqual(results["fusion_method"], "weighted")
        self.assertGreater(len(results["results"]), 0)
        
        # Verificar que los resultados tienen el formato correcto
        for result in results["results"]:
            self.assertIn("fusion_method", result)
            self.assertEqual(result["fusion_method"], "weighted")
    
    def test_deduplication(self):
        """Probar deduplicación de resultados"""
        results = self.fusion.search("viáticos nacionales", top_k=5)
        
        # Verificar que no hay duplicados por ID
        doc_ids = [result["id"] for result in results["results"]]
        self.assertEqual(len(doc_ids), len(set(doc_ids)))
    
    def test_add_retriever(self):
        """Probar agregar un retriever"""
        mock_new = MockRetriever("new", [
            {"id": "doc5", "text": "Nuevo documento", "score": 0.8}
        ])
        
        initial_count = len(self.fusion.retrievers)
        self.fusion.add_retriever("new", mock_new, weight=0.5)
        
        self.assertEqual(len(self.fusion.retrievers), initial_count + 1)
        self.assertIn("new", self.fusion.retrievers)
        self.assertIn("new", self.fusion.weights)
    
    def test_remove_retriever(self):
        """Probar remover un retriever"""
        initial_count = len(self.fusion.retrievers)
        self.fusion.remove_retriever("bm25")
        
        self.assertEqual(len(self.fusion.retrievers), initial_count - 1)
        self.assertNotIn("bm25", self.fusion.retrievers)
        self.assertNotIn("bm25", self.fusion.weights)
    
    def test_empty_results(self):
        """Probar manejo de resultados vacíos"""
        empty_retriever = MockRetriever("empty", [])
        fusion_empty = HybridFusion(
            retrievers={"empty": empty_retriever},
            method="rrf"
        )
        
        results = fusion_empty.search("consulta", top_k=5)
        
        self.assertEqual(len(results["results"]), 0)
        self.assertIsInstance(results["results"], list)
    
    def test_normalize_results(self):
        """Probar normalización de resultados"""
        # Crear resultados con formato diferente
        different_format_results = {
            "results": [
                {"texto": "Documento 1", "puntuacion": 0.9},
                {"contenido": "Documento 2", "score": 0.8}
            ]
        }
        
        normalized = self.fusion._normalize_results(different_format_results, "test")
        
        self.assertIsInstance(normalized, list)
        for item in normalized:
            self.assertIn("text", item)
            self.assertIn("score", item)
            self.assertIn("source_retriever", item)
    
    def test_document_key_generation(self):
        """Probar generación de claves de documento"""
        doc = {"id": "test_id", "text": "test text"}
        key = self.fusion._get_document_key(doc)
        
        self.assertEqual(key, "test_id")
        
        # Probar sin ID
        doc_no_id = {"text": "test text"}
        key_no_id = self.fusion._get_document_key(doc_no_id)
        
        self.assertIsInstance(key_no_id, str)
        self.assertGreater(len(key_no_id), 0)


class TestMockRetriever(unittest.TestCase):
    """Pruebas para el MockRetriever"""
    
    def test_mock_retriever(self):
        """Probar funcionalidad del MockRetriever"""
        mock_results = [
            {"id": "doc1", "text": "Test document", "score": 0.9}
        ]
        
        retriever = MockRetriever("test", mock_results)
        
        results = retriever.search("test query")
        
        self.assertIn("results", results)
        self.assertEqual(results["results"], mock_results)


class TestHybridFusionIntegration(unittest.TestCase):
    """Pruebas de integración para el sistema híbrido"""
    
    def test_full_search_pipeline(self):
        """Probar pipeline completo de búsqueda híbrida"""
        # Crear retrievers con diferentes características
        bm25_results = [
            {"id": f"doc{i}", "text": f"Documento BM25 {i}", "score": 0.9 - i*0.1}
            for i in range(1, 4)
        ]
        
        dense_results = [
            {"id": f"doc{i+1}", "text": f"Documento Dense {i+1}", "score": 0.95 - i*0.1}
            for i in range(3)
        ]
        
        bm25_retriever = MockRetriever("bm25", bm25_results)
        dense_retriever = MockRetriever("dense", dense_results)
        
        # Crear sistema de fusión
        fusion = HybridFusion(
            retrievers={"bm25": bm25_retriever, "dense": dense_retriever},
            method="rrf",
            weights={"bm25": 0.6, "dense": 0.4}
        )
        
        # Ejecutar búsqueda
        results = fusion.search("test query", top_k=5)
        
        # Verificaciones
        self.assertIsInstance(results, dict)
        self.assertIn("query", results)
        self.assertIn("results", results)
        self.assertIn("time_taken", results)
        self.assertIn("retriever_times", results)
        
        # Verificar que hay resultados
        self.assertGreater(len(results["results"]), 0)
        
        # Verificar que los resultados están ordenados por score
        scores = [result["score"] for result in results["results"]]
        self.assertEqual(scores, sorted(scores, reverse=True))
        
        # Verificar que cada resultado tiene fuentes de fusión
        for result in results["results"]:
            self.assertIn("fusion_sources", result)
            self.assertIsInstance(result["fusion_sources"], list)
            self.assertGreater(len(result["fusion_sources"]), 0)


if __name__ == '__main__':
    unittest.main() 