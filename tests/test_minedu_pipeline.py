#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pruebas unitarias para el MineduPipeline.

Autor: Hanns
Fecha: 2025-06-14
"""

import unittest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipelines.minedu_pipeline import MineduPipeline


class TestMineduPipeline(unittest.TestCase):
    """Pruebas para el MineduPipeline"""
    
    def setUp(self):
        """Configurar el test"""
        # Mock de configuraciones para testing
        self.mock_config = {
            'vectorstore_path': 'test/path/vectorstore.pkl',
            'chunks_path': 'test/path/chunks.json',
            'max_results': 5,
            'security_enabled': True
        }
        
        # Crear pipeline con mocks
        with patch('src.pipelines.minedu_pipeline.SecurityConfig') as mock_security:
            with patch('src.pipelines.minedu_pipeline.SecureHybridSearch') as mock_search:
                mock_security.return_value = Mock()
                mock_search.return_value = Mock()
                
                self.pipeline = MineduPipeline(config=self.mock_config)
    
    def test_initialization(self):
        """Probar inicialización del pipeline"""
        self.assertIsNotNone(self.pipeline)
        self.assertEqual(self.pipeline.config, self.mock_config)
        self.assertIsNotNone(self.pipeline.security_config)
        self.assertIsNotNone(self.pipeline.search_system)
    
    def test_validate_query(self):
        """Probar validación de consultas"""
        # Consulta válida
        valid_query = "¿Cuál es el monto máximo para viáticos?"
        self.assertTrue(self.pipeline.validate_query(valid_query))
        
        # Consulta vacía
        empty_query = ""
        self.assertFalse(self.pipeline.validate_query(empty_query))
        
        # Consulta con solo espacios
        whitespace_query = "   \n\t   "
        self.assertFalse(self.pipeline.validate_query(whitespace_query))
    
    def test_search_documents(self):
        """Probar búsqueda de documentos"""
        query = "viáticos nacionales"
        
        # Mock de resultados
        mock_results = [
            {
                "id": "doc1",
                "text": "Documento sobre viáticos nacionales",
                "score": 0.9,
                "method": "hybrid"
            },
            {
                "id": "doc2", 
                "text": "Documento sobre autorización de gastos",
                "score": 0.8,
                "method": "hybrid"
            }
        ]
        
        # Configurar mock del sistema de búsqueda
        self.pipeline.search_system.search.return_value = (mock_results, None)
        
        # Ejecutar búsqueda
        results, error = self.pipeline.search_documents(query)
        
        # Verificaciones
        self.assertIsNone(error)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)
        
        # Verificar formato de resultados
        for result in results:
            self.assertIn("id", result)
            self.assertIn("text", result)
            self.assertIn("score", result)
            self.assertIn("method", result)
    
    def test_search_documents_with_error(self):
        """Probar búsqueda con error"""
        query = "consulta de prueba"
        
        # Configurar mock para devolver error
        self.pipeline.search_system.search.return_value = ([], "Error de búsqueda")
        
        # Ejecutar búsqueda
        results, error = self.pipeline.search_documents(query)
        
        # Verificaciones
        self.assertIsNotNone(error)
        self.assertEqual(error, "Error de búsqueda")
        self.assertEqual(results, [])
    
    def test_process_query(self):
        """Probar procesamiento completo de consulta"""
        query = "¿Cuál es el monto máximo para viáticos nacionales?"
        
        # Mock de resultados
        mock_results = [
            {
                "id": "doc1",
                "text": "El monto máximo diario para viáticos nacionales es S/ 150.00",
                "score": 0.95,
                "method": "hybrid"
            }
        ]
        
        # Configurar mocks
        self.pipeline.search_system.search.return_value = (mock_results, None)
        
        # Ejecutar procesamiento
        response = self.pipeline.process_query(query)
        
        # Verificaciones
        self.assertIsInstance(response, dict)
        self.assertIn("success", response)
        self.assertIn("query", response)
        self.assertIn("results", response)
        self.assertIn("metadata", response)
        
        self.assertTrue(response["success"])
        self.assertEqual(response["query"], query)
        self.assertEqual(len(response["results"]), 1)
    
    def test_process_query_invalid(self):
        """Probar procesamiento de consulta inválida"""
        invalid_query = ""
        
        response = self.pipeline.process_query(invalid_query)
        
        self.assertIsInstance(response, dict)
        self.assertIn("success", response)
        self.assertFalse(response["success"])
        self.assertIn("error", response)
    
    def test_get_system_status(self):
        """Probar obtención de estado del sistema"""
        status = self.pipeline.get_system_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn("pipeline_status", status)
        self.assertIn("security_status", status)
        self.assertIn("search_system_status", status)
    
    def test_validate_config(self):
        """Probar validación de configuración"""
        # Configuración válida
        valid_config = {
            'vectorstore_path': 'test/path/vectorstore.pkl',
            'max_results': 5
        }
        
        self.assertTrue(self.pipeline.validate_config(valid_config))
        
        # Configuración inválida
        invalid_config = {}
        self.assertFalse(self.pipeline.validate_config(invalid_config))
    
    def test_error_handling(self):
        """Probar manejo de errores"""
        query = "consulta de prueba"
        
        # Simular excepción en el sistema de búsqueda
        self.pipeline.search_system.search.side_effect = Exception("Error interno")
        
        # Ejecutar búsqueda
        results, error = self.pipeline.search_documents(query)
        
        # Verificaciones
        self.assertIsNotNone(error)
        self.assertEqual(results, [])
    
    def test_metadata_generation(self):
        """Probar generación de metadatos"""
        query = "consulta de prueba"
        
        # Mock de resultados
        mock_results = [
            {
                "id": "doc1",
                "text": "Documento de prueba",
                "score": 0.9,
                "method": "hybrid"
            }
        ]
        
        # Configurar mock
        self.pipeline.search_system.search.return_value = (mock_results, None)
        
        # Ejecutar búsqueda
        response = self.pipeline.process_query(query)
        
        # Verificar metadatos
        metadata = response["metadata"]
        self.assertIn("timestamp", metadata)
        self.assertIn("query_length", metadata)
        self.assertIn("results_count", metadata)
        self.assertIn("execution_time", metadata)
    
    def test_security_integration(self):
        """Probar integración con seguridad"""
        query = "consulta de prueba"
        
        # Verificar que se usa la configuración de seguridad
        self.assertIsNotNone(self.pipeline.security_config)
        
        # Mock de validación de seguridad
        with patch.object(self.pipeline.security_config, 'validate_path') as mock_validate:
            mock_validate.return_value = True
            
            # Ejecutar búsqueda
            results, error = self.pipeline.search_documents(query)
            
            # Verificar que se llamó la validación
            mock_validate.assert_called()


class TestMineduPipelineIntegration(unittest.TestCase):
    """Pruebas de integración para el MineduPipeline"""
    
    def test_full_pipeline_execution(self):
        """Probar ejecución completa del pipeline"""
        # Configuración completa
        config = {
            'vectorstore_path': 'test/path/vectorstore.pkl',
            'chunks_path': 'test/path/chunks.json',
            'max_results': 3,
            'security_enabled': True,
            'log_level': 'INFO'
        }
        
        # Mock de componentes
        with patch('src.pipelines.minedu_pipeline.SecurityConfig') as mock_security:
            with patch('src.pipelines.minedu_pipeline.SecureHybridSearch') as mock_search:
                mock_security.return_value = Mock()
                mock_search.return_value = Mock()
                
                pipeline = MineduPipeline(config=config)
                
                # Mock de resultados
                mock_results = [
                    {
                        "id": "doc1",
                        "text": "Documento sobre viáticos",
                        "score": 0.9,
                        "method": "hybrid"
                    }
                ]
                
                pipeline.search_system.search.return_value = (mock_results, None)
                
                # Ejecutar pipeline completo
                response = pipeline.process_query("viáticos nacionales")
                
                # Verificaciones
                self.assertTrue(response["success"])
                self.assertIn("results", response)
                self.assertIn("metadata", response)
                
                # Verificar que se llamaron los componentes correctos
                pipeline.search_system.search.assert_called_once()
    
    def test_pipeline_with_multiple_queries(self):
        """Probar pipeline con múltiples consultas"""
        with patch('src.pipelines.minedu_pipeline.SecurityConfig') as mock_security:
            with patch('src.pipelines.minedu_pipeline.SecureHybridSearch') as mock_search:
                mock_security.return_value = Mock()
                mock_search.return_value = Mock()
                
                pipeline = MineduPipeline(config=self.mock_config)
                
                queries = [
                    "viáticos nacionales",
                    "autorización de gastos",
                    "rendición de cuentas"
                ]
                
                for query in queries:
                    # Mock de resultados diferentes para cada consulta
                    mock_results = [
                        {
                            "id": f"doc_{query[:5]}",
                            "text": f"Documento sobre {query}",
                            "score": 0.9,
                            "method": "hybrid"
                        }
                    ]
                    
                    pipeline.search_system.search.return_value = (mock_results, None)
                    
                    # Procesar consulta
                    response = pipeline.process_query(query)
                    
                    # Verificaciones
                    self.assertTrue(response["success"])
                    self.assertEqual(response["query"], query)
                    self.assertEqual(len(response["results"]), 1)


if __name__ == '__main__':
    unittest.main() 