#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pruebas unitarias para el preprocesamiento y limpieza de texto.

Autor: Hanns
Fecha: 2025-06-14
"""

import unittest
import sys
import os
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.text_processor.text_cleaner_v2 import TextCleaner
from src.text_processor.text_chunker_v2 import TextChunker


class TestTextCleaner(unittest.TestCase):
    """Pruebas para la limpieza de texto"""
    
    def setUp(self):
        """Configurar el test"""
        self.cleaner = TextCleaner()
    
    def test_basic_cleaning(self):
        """Probar limpieza básica de texto"""
        dirty_text = "  Este es un   texto   con   espacios   extra   y   saltos\n\n\n\n  "
        expected = "Este es un texto con espacios extra y saltos"
        
        result = self.cleaner.clean_text(dirty_text)
        self.assertEqual(result, expected)
    
    def test_remove_special_characters(self):
        """Probar eliminación de caracteres especiales"""
        text_with_special = "Texto con @#$%^&*() caracteres especiales"
        expected = "Texto con caracteres especiales"
        
        result = self.cleaner.clean_text(text_with_special)
        self.assertEqual(result, expected)
    
    def test_normalize_whitespace(self):
        """Probar normalización de espacios en blanco"""
        text_with_whitespace = "Texto\tcon\ttabulaciones\ty\nsaltos\nde\nlínea"
        expected = "Texto con tabulaciones y saltos de línea"
        
        result = self.cleaner.clean_text(text_with_whitespace)
        self.assertEqual(result, expected)
    
    def test_empty_text(self):
        """Probar manejo de texto vacío"""
        result = self.cleaner.clean_text("")
        self.assertEqual(result, "")
        
        result = self.cleaner.clean_text("   \n\t   ")
        self.assertEqual(result, "")
    
    def test_preserve_important_chars(self):
        """Probar preservación de caracteres importantes"""
        text_with_important = "Texto con números 123, puntos. y comas,"
        result = self.cleaner.clean_text(text_with_important)
        
        # Debería preservar números, puntos y comas
        self.assertIn("123", result)
        self.assertIn(".", result)
        self.assertIn(",", result)


class TestTextChunker(unittest.TestCase):
    """Pruebas para el chunking de texto"""
    
    def setUp(self):
        """Configurar el test"""
        self.chunker = TextChunker()
    
    def test_basic_chunking(self):
        """Probar chunking básico"""
        text = "Este es el primer párrafo. Este es el segundo párrafo. Este es el tercer párrafo."
        
        chunks = self.chunker.create_chunks(text, chunk_size=50, overlap=10)
        
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0)
        
        # Verificar que cada chunk tiene el formato correcto
        for chunk in chunks:
            self.assertIsInstance(chunk, dict)
            self.assertIn('text', chunk)
            self.assertIn('metadata', chunk)
    
    def test_chunk_size_respect(self):
        """Probar que se respeta el tamaño de chunk"""
        text = "Este es un texto largo que debería ser dividido en chunks más pequeños. " * 10
        
        chunks = self.chunker.create_chunks(text, chunk_size=100, overlap=0)
        
        for chunk in chunks:
            self.assertLessEqual(len(chunk['text']), 100)
    
    def test_overlap_functionality(self):
        """Probar funcionalidad de overlap"""
        text = "Párrafo uno. Párrafo dos. Párrafo tres. Párrafo cuatro."
        
        chunks = self.chunker.create_chunks(text, chunk_size=30, overlap=10)
        
        # Verificar que hay overlap entre chunks consecutivos
        if len(chunks) > 1:
            for i in range(len(chunks) - 1):
                current_chunk = chunks[i]['text']
                next_chunk = chunks[i + 1]['text']
                
                # Debería haber alguna superposición
                self.assertTrue(
                    any(word in next_chunk for word in current_chunk.split()[-3:]),
                    f"No hay overlap entre chunks {i} y {i+1}"
                )
    
    def test_metadata_generation(self):
        """Probar generación de metadatos"""
        text = "Texto de prueba para metadatos."
        
        chunks = self.chunker.create_chunks(text, chunk_size=50, overlap=0)
        
        for i, chunk in enumerate(chunks):
            metadata = chunk['metadata']
            self.assertIn('chunk_id', metadata)
            self.assertIn('chunk_index', metadata)
            self.assertEqual(metadata['chunk_index'], i)
    
    def test_empty_text_chunking(self):
        """Probar chunking de texto vacío"""
        chunks = self.chunker.create_chunks("", chunk_size=50, overlap=0)
        self.assertEqual(chunks, [])
    
    def test_small_text_chunking(self):
        """Probar chunking de texto pequeño"""
        text = "Texto pequeño"
        chunks = self.chunker.create_chunks(text, chunk_size=100, overlap=0)
        
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]['text'], text)


class TestTextProcessorIntegration(unittest.TestCase):
    """Pruebas de integración para el procesamiento de texto"""
    
    def setUp(self):
        """Configurar el test"""
        self.cleaner = TextCleaner()
        self.chunker = TextChunker()
    
    def test_full_pipeline(self):
        """Probar pipeline completo de procesamiento"""
        dirty_text = """
        Este es un   texto   sucio   con   espacios   extra.
        
        Tiene @#$%^&*() caracteres especiales.
        
        Y múltiples saltos de línea.
        """
        
        # Paso 1: Limpiar
        clean_text = self.cleaner.clean_text(dirty_text)
        
        # Paso 2: Chunking
        chunks = self.chunker.create_chunks(clean_text, chunk_size=50, overlap=10)
        
        # Verificaciones
        self.assertIsInstance(clean_text, str)
        self.assertGreater(len(clean_text), 0)
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0)
        
        # Verificar que el texto limpio no tiene caracteres especiales
        self.assertNotIn("@#$%^&*()", clean_text)
        
        # Verificar que los chunks tienen el formato correcto
        for chunk in chunks:
            self.assertIn('text', chunk)
            self.assertIn('metadata', chunk)
            self.assertGreater(len(chunk['text']), 0)


if __name__ == '__main__':
    unittest.main() 