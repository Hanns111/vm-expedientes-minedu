#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Filtro de calidad para chunks de texto del proyecto vm-expedientes-minedu.
Este script limpia y filtra chunks de baja calidad, identificando y corrigiendo
problemas como texto corrupto, fragmentado o con errores de OCR.
"""

import os
import sys
import json
import re
import logging
from typing import Dict, List, Any, Tuple
from pathlib import Path
import string
import argparse

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/chunk_quality_filter.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ChunkQualityFilter")

# Asegurar que existe el directorio de logs
os.makedirs("logs", exist_ok=True)

class ChunkQualityFilter:
    """Filtro de calidad para chunks de texto."""
    
    def __init__(self, input_path: str, output_path: str):
        """
        Inicializa el filtro de calidad.
        
        Args:
            input_path: Ruta al archivo JSON con los chunks originales
            output_path: Ruta donde se guardarán los chunks filtrados
        """
        self.input_path = input_path
        self.output_path = output_path
        self.chunks = []
        self.cleaned_chunks = []
        self.problematic_chunks = []
        self.ocr_patterns = [
            r'\(\s*\d+\s*%\)',  # Patrones como "( 3%)"
            r'del\s+del',       # Repeticiones como "del del"
            r'S\s+O\s+LE\s+S',  # Texto espaciado como "S O LE S"
            r'\d+/\s*\d+\s+\d+' # Números fragmentados como "00/ 1 00"
        ]
        
    def load_chunks(self) -> None:
        """Carga los chunks desde el archivo JSON."""
        try:
            logger.info(f"Cargando chunks desde {self.input_path}")
            with open(self.input_path, 'r', encoding='utf-8') as f:
                self.chunks = json.load(f)
            logger.info(f"Se cargaron {len(self.chunks)} chunks")
        except Exception as e:
            logger.error(f"Error al cargar chunks: {e}")
            raise
    
    def count_special_chars(self, text: str) -> int:
        """
        Cuenta caracteres especiales en un texto.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Número de caracteres especiales
        """
        if not text:
            return 0
        
        # Considerar como especiales los que no son alfanuméricos ni espacios
        special_chars = sum(1 for char in text if not char.isalnum() and not char.isspace())
        return special_chars
    
    def count_short_words(self, text: str) -> Tuple[int, int]:
        """
        Cuenta palabras cortas (menos de 3 caracteres) en un texto.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Tupla con (número de palabras cortas, número total de palabras)
        """
        if not text:
            return (0, 0)
        
        words = text.split()
        short_words = sum(1 for word in words if len(word) < 3)
        return (short_words, len(words))
    
    def check_ocr_patterns(self, text: str) -> List[str]:
        """
        Verifica patrones típicos de OCR corrupto.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Lista de patrones encontrados
        """
        if not text:
            return []
        
        found_patterns = []
        for pattern in self.ocr_patterns:
            if re.search(pattern, text):
                found_patterns.append(pattern)
        
        return found_patterns
    
    def is_quality_chunk(self, text: str) -> bool:
        """
        Determina si un chunk tiene calidad suficiente.
        
        Args:
            text: Texto del chunk
            
        Returns:
            True si el chunk tiene calidad suficiente, False en caso contrario
        """
        if not text:
            return False
            
        # Filtro 1: Máximo 30% caracteres especiales (criterio relajado)
        special_ratio = self.count_special_chars(text) / len(text)
        if special_ratio > 0.3:
            return False
        
        # Filtro 2: Mínimo 40% palabras coherentes (>= 3 chars) (criterio relajado)
        words = text.split()
        if not words:
            return False
            
        coherent_words = [w for w in words if len(w) >= 3 and w.isalpha()]
        coherent_ratio = len(coherent_words) / len(words) if words else 0
        if coherent_ratio < 0.4:
            return False
        
        # Filtro 3: Máximo 1 patrón OCR típico (criterio relajado)
        ocr_patterns = self.check_ocr_patterns(text)
        if len(ocr_patterns) > 1:
            return False
             
        return True
    
    def clean_text(self, text: str) -> str:
        """
        Limpia un texto para mejorar su calidad.
        
        Args:
            text: Texto a limpiar
            
        Returns:
            Texto limpiado
        """
        if not text:
            return ""
        
        # 1. Eliminar patrones OCR problemáticos
        for pattern in self.ocr_patterns:
            text = re.sub(pattern, " ", text)
        
        # 2. Normalizar espacios múltiples
        text = re.sub(r'\s+', ' ', text)
        
        # 3. Eliminar caracteres no imprimibles
        text = ''.join(char for char in text if char.isprintable())
        
        # 4. Eliminar palabras muy cortas (1 carácter)
        words = text.split()
        words = [w for w in words if len(w) > 1]
        text = ' '.join(words)
        
        return text.strip()
    
    def process_chunks(self) -> None:
        """Procesa los chunks para mejorar su calidad."""
        logger.info("Procesando chunks para mejorar calidad...")
        
        for i, chunk in enumerate(self.chunks):
            # Obtener texto del chunk (usando 'texto' o 'text' como fallback)
            text = chunk.get('texto', chunk.get('text', ''))
            
            if not text:
                self.problematic_chunks.append({
                    **chunk,
                    'issue': 'No text content'
                })
                continue
            
            # Verificar calidad
            if self.is_quality_chunk(text):
                # El chunk ya tiene buena calidad
                self.cleaned_chunks.append(chunk)
            else:
                # Intentar limpiar el chunk
                cleaned_text = self.clean_text(text)
                
                # Verificar si la limpieza mejoró la calidad
                if self.is_quality_chunk(cleaned_text):
                    # La limpieza fue exitosa
                    cleaned_chunk = chunk.copy()
                    cleaned_chunk['texto'] = cleaned_text
                    cleaned_chunk['cleaned'] = True
                    self.cleaned_chunks.append(cleaned_chunk)
                else:
                    # La limpieza no fue suficiente, marcar como problemático
                    self.problematic_chunks.append({
                        **chunk,
                        'issue': 'Low quality text, cleaning failed'
                    })
            
            if i % 100 == 0 and i > 0:
                logger.info(f"Procesados {i} chunks...")
        
        logger.info(f"Procesamiento completado:")
        logger.info(f"- Chunks de alta calidad: {len(self.cleaned_chunks)}")
        logger.info(f"- Chunks problemáticos: {len(self.problematic_chunks)}")
    
    def save_cleaned_chunks(self) -> None:
        """Guarda los chunks limpios en un archivo JSON."""
        try:
            logger.info(f"Guardando chunks limpios en {self.output_path}")
            with open(self.output_path, 'w', encoding='utf-8') as f:
                json.dump(self.cleaned_chunks, f, indent=2, ensure_ascii=False)
            logger.info(f"Se guardaron {len(self.cleaned_chunks)} chunks limpios")
        except Exception as e:
            logger.error(f"Error al guardar chunks limpios: {e}")
            raise
    
    def save_problematic_chunks(self) -> None:
        """Guarda los chunks problemáticos en un archivo JSON para revisión manual."""
        try:
            problematic_path = self.output_path.replace('.json', '_problematic.json')
            logger.info(f"Guardando chunks problemáticos en {problematic_path}")
            with open(problematic_path, 'w', encoding='utf-8') as f:
                json.dump(self.problematic_chunks, f, indent=2, ensure_ascii=False)
            logger.info(f"Se guardaron {len(self.problematic_chunks)} chunks problemáticos")
        except Exception as e:
            logger.error(f"Error al guardar chunks problemáticos: {e}")
            raise
    
    def run(self) -> None:
        """Ejecuta el proceso completo de filtrado y limpieza."""
        self.load_chunks()
        self.process_chunks()
        self.save_cleaned_chunks()
        self.save_problematic_chunks()
        
        # Imprimir resumen
        print("\n" + "="*50)
        print("RESUMEN DE LIMPIEZA DE CHUNKS")
        print("="*50)
        print(f"\nTotal de chunks procesados: {len(self.chunks)}")
        print(f"Chunks de alta calidad: {len(self.cleaned_chunks)} ({len(self.cleaned_chunks)/len(self.chunks)*100:.2f}%)")
        print(f"Chunks problemáticos: {len(self.problematic_chunks)} ({len(self.problematic_chunks)/len(self.chunks)*100:.2f}%)")
        print(f"\nChunks limpios guardados en: {self.output_path}")
        print(f"Chunks problemáticos guardados en: {self.output_path.replace('.json', '_problematic.json')}")
        print("="*50 + "\n")

def parse_args():
    """Parsea los argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description='Filtro de calidad para chunks de texto')
    parser.add_argument('--input', '-i', type=str, 
                        default='data/processed/chunks_v2.json',
                        help='Ruta al archivo JSON con los chunks originales')
    parser.add_argument('--output', '-o', type=str, 
                        default='data/processed/chunks_v2_cleaned.json',
                        help='Ruta donde se guardarán los chunks filtrados')
    return parser.parse_args()

def main():
    """Función principal"""
    args = parse_args()
    
    # Definir rutas
    base_dir = Path(__file__).resolve().parent.parent.parent
    input_path = base_dir / args.input
    output_path = base_dir / args.output
    
    # Verificar existencia de archivo de entrada
    if not input_path.exists():
        logger.error(f"Archivo de entrada no encontrado: {input_path}")
        sys.exit(1)
    
    # Crear directorio de salida si no existe
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Ejecutar filtro de calidad
    filter = ChunkQualityFilter(str(input_path), str(output_path))
    filter.run()

if __name__ == "__main__":
    main()
