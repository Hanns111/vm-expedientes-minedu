#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de generación de chunks para el Sistema de Búsqueda Híbrido MINEDU.

Este script procesa documentos y genera chunks para el sistema de búsqueda.
"""

import json
import re
import logging
from pathlib import Path
from typing import List, Dict, Any


class ChunkGenerator:
    """
    Generador de chunks para documentos.
    """
    
    def __init__(self):
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Configurar logging."""
        logger = logging.getLogger('ChunkGenerator')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def clean_text(self, text: str) -> str:
        """
        Limpiar y normalizar texto.
        
        Args:
            text (str): Texto a limpiar
            
        Returns:
            str: Texto limpio
        """
        if not text:
            return ""
        
        # Convertir a minúsculas
        text = text.lower()
        
        # Remover caracteres especiales pero preservar acentos
        text = re.sub(r'[^a-záéíóúüñ\s]', ' ', text)
        
        # Normalizar espacios
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def create_chunks_from_text(self, text: str, chunk_size: int = 512, overlap: int = 50) -> List[Dict[str, Any]]:
        """
        Crear chunks a partir de texto.
        
        Args:
            text (str): Texto a dividir en chunks
            chunk_size (int): Tamaño de cada chunk
            overlap (int): Superposición entre chunks
            
        Returns:
            List[Dict[str, Any]]: Lista de chunks
        """
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            if chunk_text.strip():
                chunk = {
                    'id': len(chunks) + 1,
                    'texto': chunk_text,
                    'titulo': f'Chunk {len(chunks) + 1}',
                    'metadatos': {
                        'start_word': i,
                        'end_word': min(i + chunk_size, len(words)),
                        'word_count': len(chunk_words)
                    }
                }
                chunks.append(chunk)
        
        return chunks
    
    def create_sample_chunks(self) -> List[Dict[str, Any]]:
        """
        Crear chunks de ejemplo basados en la Directiva N° 011-2020-MINEDU.
        
        Returns:
            List[Dict[str, Any]]: Lista de chunks de ejemplo
        """
        sample_texts = [
            {
                "texto": "El monto máximo diario para viáticos nacionales es de S/ 320.00 según la escala vigente establecida en el Decreto Supremo N° 007-2013-EF.",
                "titulo": "Escala de Viáticos Nacionales",
                "section": "viáticos"
            },
            {
                "texto": "Los viáticos deben ser solicitados con diez (10) días hábiles de anticipación a la fecha programada para el viaje, salvo casos fortuitos o de fuerza mayor.",
                "titulo": "Plazo de Solicitud de Viáticos",
                "section": "solicitud"
            },
            {
                "texto": "El comisionado debe presentar una Declaración Jurada de Gastos para sustentar los gastos realizados durante la comisión de servicio.",
                "titulo": "Declaración Jurada de Gastos",
                "section": "rendición"
            },
            {
                "texto": "La autorización de viáticos corresponde al Jefe del órgano o unidad orgánica correspondiente, previa evaluación de la justificación técnica.",
                "titulo": "Autorización de Viáticos",
                "section": "autorización"
            },
            {
                "texto": "Los gastos de viáticos se rinden dentro de los cinco (5) días hábiles posteriores al término de la comisión, presentando los comprobantes correspondientes.",
                "titulo": "Plazo de Rendición",
                "section": "rendición"
            },
            {
                "texto": "El comisionado tiene la responsabilidad de utilizar los viáticos únicamente para los gastos autorizados y justificar adecuadamente su uso.",
                "titulo": "Responsabilidades del Comisionado",
                "section": "responsabilidades"
            },
            {
                "texto": "En caso de no rendir los viáticos a tiempo, el comisionado deberá devolver el monto correspondiente y podrá ser sujeto a acciones administrativas.",
                "titulo": "Consecuencias por Incumplimiento",
                "section": "sanciones"
            },
            {
                "texto": "Los viáticos para viajes internacionales se rigen por disposiciones específicas y requieren autorización especial del nivel correspondiente.",
                "titulo": "Viáticos Internacionales",
                "section": "internacionales"
            }
        ]
        
        chunks = []
        for i, sample in enumerate(sample_texts, 1):
            chunk = {
                'id': i,
                'texto': sample['texto'],
                'titulo': sample['titulo'],
                'metadatos': {
                    'page': i,
                    'type': 'normativa',
                    'section': sample['section'],
                    'source': 'Directiva N° 011-2020-MINEDU'
                }
            }
            chunks.append(chunk)
        
        return chunks
    
    def save_chunks(self, chunks: List[Dict[str, Any]], output_path: str = "data/processed/chunks.json") -> None:
        """
        Guardar chunks en archivo JSON.
        
        Args:
            chunks (List[Dict[str, Any]]): Lista de chunks a guardar
            output_path (str): Ruta de salida
        """
        # Crear directorio si no existe
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Guardar chunks
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Chunks guardados en {output_path} ({len(chunks)} fragmentos)")
    
    def generate_chunks(self, output_path: str = "data/processed/chunks.json") -> None:
        """
        Generar chunks de ejemplo y guardarlos.
        
        Args:
            output_path (str): Ruta de salida para los chunks
        """
        self.logger.info("Generando chunks de ejemplo...")
        
        chunks = self.create_sample_chunks()
        self.save_chunks(chunks, output_path)
        
        self.logger.info(f"✅ Chunks generados exitosamente: {len(chunks)} fragmentos")


def main():
    """Función principal."""
    print("🚀 GENERADOR DE CHUNKS - MINEDU SEARCH SYSTEM")
    print("=" * 50)
    
    try:
        generator = ChunkGenerator()
        generator.generate_chunks()
        
        print("\n✅ CHUNKS GENERADOS")
        print("=" * 50)
        print("📁 Archivo generado: data/processed/chunks.json")
        print("💡 Ahora puedes ejecutar: python src/data_pipeline/generate_vectorstores.py")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main() 