#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Diagnóstico de calidad de chunks para el proyecto vm-expedientes-minedu.
Este script analiza los chunks procesados para identificar problemas de calidad
como texto corrupto, fragmentado o con errores de OCR.
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
        logging.FileHandler("logs/chunks_quality_diagnosis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ChunksQualityDiagnostic")

# Asegurar que existe el directorio de logs
os.makedirs("logs", exist_ok=True)

class ChunkQualityDiagnostic:
    """Diagnóstico de calidad de chunks de texto."""
    
    def __init__(self, chunks_path: str, output_path: str):
        """
        Inicializa el diagnóstico de calidad.
        
        Args:
            chunks_path: Ruta al archivo JSON con los chunks procesados
            output_path: Ruta donde se guardará el reporte de calidad
        """
        self.chunks_path = chunks_path
        self.output_path = output_path
        self.chunks = []
        self.quality_metrics = []
        self.ocr_patterns = [
            r'\(\s*\d+\s*%\)',  # Patrones como "( 3%)"
            r'del\s+del',       # Repeticiones como "del del"
            r'S\s+O\s+LE\s+S',  # Texto espaciado como "S O LE S"
            r'\d+/\s*\d+\s+\d+' # Números fragmentados como "00/ 1 00"
        ]
        
    def load_chunks(self) -> None:
        """Carga los chunks desde el archivo JSON."""
        try:
            logger.info(f"Cargando chunks desde {self.chunks_path}")
            with open(self.chunks_path, 'r', encoding='utf-8') as f:
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
    
    def analyze_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza la calidad de un chunk.
        
        Args:
            chunk: Chunk a analizar
            
        Returns:
            Diccionario con métricas de calidad
        """
        # Obtener texto del chunk (usando 'texto' o 'text' como fallback)
        text = chunk.get('texto', chunk.get('text', ''))
        
        if not text:
            return {
                'id': chunk.get('id', 'unknown'),
                'quality_score': 0,
                'is_corrupt': True,
                'reason': 'No text content',
                'special_char_ratio': 1.0,
                'short_word_ratio': 1.0,
                'ocr_patterns': [],
                'length': 0
            }
        
        # Calcular métricas
        special_chars = self.count_special_chars(text)
        special_ratio = special_chars / len(text) if len(text) > 0 else 1.0
        
        short_words, total_words = self.count_short_words(text)
        short_word_ratio = short_words / total_words if total_words > 0 else 1.0
        
        ocr_patterns = self.check_ocr_patterns(text)
        
        # Determinar si el chunk está corrupto
        is_corrupt = (special_ratio > 0.2 or 
                      short_word_ratio > 0.3 or 
                      len(ocr_patterns) > 0)
        
        # Calcular score de calidad (0-100)
        quality_score = 100 - (
            (special_ratio * 50) +  # Penalización por caracteres especiales
            (short_word_ratio * 30) +  # Penalización por palabras cortas
            (len(ocr_patterns) * 20)  # Penalización por patrones OCR
        )
        quality_score = max(0, min(100, quality_score))  # Limitar entre 0 y 100
        
        # Determinar razón principal de corrupción
        reason = []
        if special_ratio > 0.2:
            reason.append(f"Alto ratio de caracteres especiales ({special_ratio:.2f})")
        if short_word_ratio > 0.3:
            reason.append(f"Alto ratio de palabras cortas ({short_word_ratio:.2f})")
        if ocr_patterns:
            reason.append(f"Patrones OCR detectados: {', '.join(ocr_patterns)}")
        
        return {
            'id': chunk.get('id', 'unknown'),
            'quality_score': quality_score,
            'is_corrupt': is_corrupt,
            'reason': '; '.join(reason) if reason else 'Good quality',
            'special_char_ratio': special_ratio,
            'short_word_ratio': short_word_ratio,
            'ocr_patterns': ocr_patterns,
            'length': len(text)
        }
    
    def analyze_all_chunks(self) -> None:
        """Analiza la calidad de todos los chunks."""
        logger.info("Analizando calidad de chunks...")
        
        for i, chunk in enumerate(self.chunks):
            metrics = self.analyze_chunk(chunk)
            self.quality_metrics.append(metrics)
            
            if i % 100 == 0 and i > 0:
                logger.info(f"Procesados {i} chunks...")
        
        logger.info(f"Análisis completado para {len(self.chunks)} chunks")
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Genera un reporte con estadísticas de calidad.
        
        Returns:
            Diccionario con estadísticas de calidad
        """
        if not self.quality_metrics:
            logger.warning("No hay métricas de calidad para generar reporte")
            return {}
        
        # Calcular estadísticas
        total_chunks = len(self.quality_metrics)
        corrupt_chunks = sum(1 for m in self.quality_metrics if m['is_corrupt'])
        corrupt_percentage = (corrupt_chunks / total_chunks) * 100 if total_chunks > 0 else 0
        
        avg_quality = sum(m['quality_score'] for m in self.quality_metrics) / total_chunks if total_chunks > 0 else 0
        
        # Clasificar chunks por calidad
        excellent = sum(1 for m in self.quality_metrics if m['quality_score'] >= 90)
        good = sum(1 for m in self.quality_metrics if 70 <= m['quality_score'] < 90)
        average = sum(1 for m in self.quality_metrics if 50 <= m['quality_score'] < 70)
        poor = sum(1 for m in self.quality_metrics if 30 <= m['quality_score'] < 50)
        very_poor = sum(1 for m in self.quality_metrics if m['quality_score'] < 30)
        
        # Identificar los 10 chunks con peor calidad
        worst_chunks = sorted(self.quality_metrics, key=lambda x: x['quality_score'])[:10]
        
        # Crear reporte
        report = {
            'total_chunks': total_chunks,
            'corrupt_chunks': corrupt_chunks,
            'corrupt_percentage': corrupt_percentage,
            'average_quality_score': avg_quality,
            'quality_distribution': {
                'excellent': excellent,
                'good': good,
                'average': average,
                'poor': poor,
                'very_poor': very_poor
            },
            'worst_chunks': worst_chunks,
            'detailed_metrics': self.quality_metrics
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any]) -> None:
        """
        Guarda el reporte en un archivo JSON.
        
        Args:
            report: Reporte a guardar
        """
        try:
            logger.info(f"Guardando reporte en {self.output_path}")
            with open(self.output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info("Reporte guardado correctamente")
        except Exception as e:
            logger.error(f"Error al guardar reporte: {e}")
            raise
    
    def print_summary(self, report: Dict[str, Any]) -> None:
        """
        Imprime un resumen del reporte.
        
        Args:
            report: Reporte a resumir
        """
        print("\n" + "="*50)
        print("DIAGNÓSTICO DE CALIDAD DE CHUNKS")
        print("="*50)
        
        print(f"\nTotal de chunks analizados: {report['total_chunks']}")
        print(f"Chunks corruptos: {report['corrupt_chunks']} ({report['corrupt_percentage']:.2f}%)")
        print(f"Score de calidad promedio: {report['average_quality_score']:.2f}/100")
        
        print("\nDistribución de calidad:")
        print(f"  Excelente (90-100): {report['quality_distribution']['excellent']} chunks")
        print(f"  Buena (70-89): {report['quality_distribution']['good']} chunks")
        print(f"  Media (50-69): {report['quality_distribution']['average']} chunks")
        print(f"  Pobre (30-49): {report['quality_distribution']['poor']} chunks")
        print(f"  Muy pobre (0-29): {report['quality_distribution']['very_poor']} chunks")
        
        print("\nChunks con peor calidad:")
        for i, chunk in enumerate(report['worst_chunks'][:5]):
            print(f"  {i+1}. ID: {chunk['id']}, Score: {chunk['quality_score']:.2f}")
            print(f"     Razón: {chunk['reason']}")
        
        print("\nReporte completo guardado en:", self.output_path)
        print("="*50 + "\n")
    
    def run(self) -> Dict[str, Any]:
        """
        Ejecuta el diagnóstico completo.
        
        Returns:
            Reporte de calidad
        """
        self.load_chunks()
        self.analyze_all_chunks()
        report = self.generate_report()
        self.save_report(report)
        self.print_summary(report)
        return report

def parse_args():
    """Parsea los argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description='Diagnóstico de calidad de chunks')
    parser.add_argument('--input', '-i', type=str, 
                        default='data/processed/chunks_v2.json',
                        help='Ruta al archivo JSON con los chunks')
    parser.add_argument('--output', '-o', type=str, 
                        default='data/processed/chunks_quality_report.json',
                        help='Ruta donde se guardará el reporte de calidad')
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
    
    # Ejecutar diagnóstico
    diagnostic = ChunkQualityDiagnostic(str(input_path), str(output_path))
    diagnostic.run()

if __name__ == "__main__":
    main()
