#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Compare All Search Systems

Este script permite comparar todos los sistemas de búsqueda implementados:
- TF-IDF (sistema original)
- BM25 (sistema paralelo)
- Sentence Transformers (fase 2)
- Sistema Híbrido (fase 4)

Uso:
    python compare_all_systems.py --methods tfidf,bm25 --query "consulta de ejemplo" --top_k 5
    python compare_all_systems.py --methods all --comprehensive --output_format json
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('SystemComparator')

# Crear directorios para resultados si no existen
os.makedirs('data/evaluation/benchmark_results/comparison_reports', exist_ok=True)
os.makedirs('logs', exist_ok=True)

class SystemComparator:
    """Clase para comparar diferentes sistemas de búsqueda."""
    
    def __init__(self, methods: List[str], top_k: int = 5, comprehensive: bool = False):
        """
        Inicializa el comparador de sistemas.
        
        Args:
            methods: Lista de métodos a comparar ('tfidf', 'bm25', 'transformers', 'hybrid')
            top_k: Número de resultados a recuperar
            comprehensive: Si es True, realiza evaluación exhaustiva con métricas adicionales
        """
        self.methods = methods
        self.top_k = top_k
        self.comprehensive = comprehensive
        self.systems = {}
        self.results = {}
        self.metrics = {}
        
        # Cargar sistemas solicitados
        self._load_systems()
    
    def _load_systems(self) -> None:
        """Carga los sistemas de búsqueda solicitados."""
        logger.info("Cargando sistemas de búsqueda...")
        
        # Cargar TF-IDF (sistema original)
        if 'tfidf' in self.methods or 'all' in self.methods:
            try:
                from search_vectorstore_hybrid import SearchVectorstore
                self.systems['tfidf'] = SearchVectorstore('data/processed/vectorstore_semantic_full_v2.pkl')
                logger.info("Sistema TF-IDF cargado correctamente")
            except Exception as e:
                logger.error(f"Error al cargar sistema TF-IDF: {e}")
        
        # Cargar BM25 (sistema paralelo)
        if 'bm25' in self.methods or 'all' in self.methods:
            try:
                from search_vectorstore_bm25 import BM25Search
                self.systems['bm25'] = BM25Search('data/processed/vectorstore_bm25_test.pkl')
                logger.info("Sistema BM25 cargado correctamente")
            except Exception as e:
                logger.error(f"Error al cargar sistema BM25: {e}")
        
        # Cargar Sentence Transformers (fase 2)
        if 'transformers' in self.methods or 'all' in self.methods:
            try:
                from search_vectorstore_transformers import TransformersSearch
                self.systems['transformers'] = TransformersSearch('data/processed/vectorstore_transformers_test.pkl')
                logger.info("Sistema Transformers cargado correctamente")
            except Exception as e:
                logger.warning(f"Sistema Transformers no disponible: {e}")
        
        # Cargar Sistema Híbrido (fase 4)
        if 'hybrid' in self.methods or 'all' in self.methods:
            try:
                from search_vectorstore_hybrid_complete import HybridSearch
                self.systems['hybrid'] = HybridSearch('data/processed/vectorstore_hybrid_final.pkl')
                logger.info("Sistema Híbrido cargado correctamente")
            except Exception as e:
                logger.warning(f"Sistema Híbrido no disponible: {e}")
        
        if not self.systems:
            logger.error("No se pudo cargar ningún sistema de búsqueda")
            sys.exit(1)
        
        logger.info("Sistemas de búsqueda cargados correctamente")
    
    def compare(self, query: str) -> Dict[str, Any]:
        """
        Compara los sistemas de búsqueda para una consulta dada.
        
        Args:
            query: Consulta a buscar
        
        Returns:
            Diccionario con resultados y métricas de comparación
        """
        logger.info(f"Comparando sistemas para consulta: '{query}'")
        
        # Ejecutar búsqueda en cada sistema
        for method, system in self.systems.items():
            start_time = time.time()
            try:
                result = system.search(query, top_k=self.top_k)
                end_time = time.time()
                
                # Verificar el formato de los resultados
                if isinstance(result, dict):
                    # Ya es un diccionario, lo usamos directamente
                    self.results[method] = result
                    self.results[method]['execution_time'] = end_time - start_time
                else:
                    # Convertir a formato de diccionario
                    self.results[method] = {
                        'results': result if isinstance(result, list) else [result],
                        'execution_time': end_time - start_time
                    }
                
                logger.info(f"Búsqueda con {method} completada en {end_time - start_time:.4f} segundos")
            except Exception as e:
                logger.error(f"Error al ejecutar búsqueda con {method}: {e}")
                self.results[method] = {'error': str(e)}
        
        # Calcular métricas de comparación
        self._calculate_metrics(query)
        
        # Generar reporte
        report = self._generate_report(query)
        
        # Guardar resultados
        self._save_results(query, report)
        
        return report
    
    def _calculate_metrics(self, query: str) -> None:
        """
        Calcula métricas de comparación entre sistemas.
        
        Args:
            query: Consulta utilizada
        """
        # Inicializar métricas
        self.metrics = {
            'execution_time': {},
            'result_count': {},
            'overlap': {},
            'top_result_match': {},
            'unique_results': {}
        }
        
        # Si no hay al menos dos sistemas, no podemos comparar
        if len(self.systems) < 2:
            logger.warning("Se necesitan al menos dos sistemas para calcular métricas de comparación")
            return
        
        # Calcular métricas para cada sistema
        for method, result in self.results.items():
            if 'error' in result:
                continue
                
            # Tiempo de ejecución
            self.metrics['execution_time'][method] = result.get('execution_time', 0)
            
            # Cantidad de resultados
            result_count = len(result.get('results', []))
            self.metrics['result_count'][method] = result_count
        
        # Calcular métricas de comparación entre sistemas
        methods = list(self.systems.keys())
        for i in range(len(methods)):
            for j in range(i+1, len(methods)):
                method1, method2 = methods[i], methods[j]
                
                # Verificar si hay resultados para ambos métodos
                if 'error' in self.results[method1] or 'error' in self.results[method2]:
                    continue
                
                # Calcular solapamiento de resultados
                results1 = self._get_result_ids(method1)
                results2 = self._get_result_ids(method2)
                
                common_results = set(results1) & set(results2)
                overlap_percentage = len(common_results) / max(len(results1), len(results2)) * 100 if results1 and results2 else 0
                
                self.metrics['overlap'][f"{method1}_vs_{method2}"] = {
                    'common_count': len(common_results),
                    'percentage': overlap_percentage
                }
                
                # Verificar si el resultado principal es el mismo
                top_match = False
                if results1 and results2:
                    top_match = results1[0] == results2[0]
                
                self.metrics['top_result_match'][f"{method1}_vs_{method2}"] = top_match
                
                # Resultados únicos
                unique_to_1 = len(set(results1) - set(results2))
                unique_to_2 = len(set(results2) - set(results1))
                
                self.metrics['unique_results'][f"unique_to_{method1}"] = unique_to_1
                self.metrics['unique_results'][f"unique_to_{method2}"] = unique_to_2
                
                # Calcular diferencia promedio de posición para resultados comunes
                if common_results:
                    position_diffs = []
                    for res_id in common_results:
                        pos1 = results1.index(res_id)
                        pos2 = results2.index(res_id)
                        position_diffs.append(abs(pos1 - pos2))
                    
                    avg_position_diff = sum(position_diffs) / len(position_diffs)
                    self.metrics['overlap'][f"{method1}_vs_{method2}"]['avg_position_diff'] = avg_position_diff
    
    def _get_result_ids(self, method: str) -> List[str]:
        """
        Obtiene los IDs de los resultados para un método dado.
        
        Args:
            method: Método de búsqueda
            
        Returns:
            Lista de IDs de resultados
        """
        results = self.results[method].get('results', [])
        
        # Verificar si hay resultados disponibles
        if not results or 'error' in self.results[method]:
            return []
        
        # Intentar extraer IDs de diferentes formas según el formato de resultados
        ids = []
        for r in results:
            if isinstance(r, dict):
                # Intentar diferentes claves que podrían contener el ID
                id_val = None
                for key in ['id', 'chunk_id', 'index', 'doc_id']:
                    if key in r:
                        id_val = r[key]
                        break
                
                # Si no se encontró ID, usar el hash del texto como identificador
                if id_val is None:
                    text = r.get('texto', r.get('text', str(r)))
                    if isinstance(text, str):
                        id_val = hash(text)
                    else:
                        id_val = hash(str(text))
                
                ids.append(str(id_val))
            else:
                ids.append(str(hash(str(r))))
        
        return ids
    
    def _generate_report(self, query: str) -> Dict[str, Any]:
        """
        Genera un reporte de comparación.
        
        Args:
            query: Consulta utilizada
            
        Returns:
            Diccionario con el reporte de comparación
        """
        report = {
            'query': query,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'systems_compared': list(self.systems.keys()),
            'metrics': self.metrics,
            'detailed_results': {}
        }
        
        # Incluir resultados detallados si se solicitó evaluación exhaustiva
        if self.comprehensive:
            for method, result in self.results.items():
                if 'error' not in result:
                    report['detailed_results'][method] = result
        
        return report
    
    def _save_results(self, query: str, report: Dict[str, Any]) -> None:
        """
        Guarda los resultados de la comparación.
        
        Args:
            query: Consulta utilizada
            report: Reporte de comparación
        """
        # Crear nombre de archivo sanitizado
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        query_sanitized = query[:20].replace(' ', '_').replace('?', '').replace('¿', '')
        filename = f"compare_{'_'.join(self.systems.keys())}_{query_sanitized}_{timestamp}.json"
        filepath = os.path.join('data/evaluation/benchmark_results/comparison_reports', filename)
        
        # Guardar reporte en formato JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Resultados guardados en: {filepath}")
    
    def print_summary(self, query: str) -> None:
        """
        Imprime un resumen de la comparación.
        
        Args:
            query: Consulta utilizada
        """
        if not self.metrics:
            logger.warning("No hay métricas disponibles para mostrar")
            return
        
        print("\n" + "=" * 50)
        print(f"COMPARACIÓN {' vs '.join(self.systems.keys()).upper()}: '{query}'")
        print("=" * 50 + "\n")
        
        # Tiempos de ejecución
        if self.metrics.get('execution_time'):
            print("TIEMPO DE EJECUCIÓN:")
            for method, time_taken in self.metrics['execution_time'].items():
                print(f"{method.upper()}: {time_taken:.4f} segundos")
            
            # Calcular diferencias de tiempo
            methods = list(self.metrics['execution_time'].keys())
            if len(methods) >= 2:
                method1, method2 = methods[0], methods[1]
                time1 = self.metrics['execution_time'][method1]
                time2 = self.metrics['execution_time'][method2]
                diff_ms = (time2 - time1) * 1000
                diff_percent = (time2 - time1) / time1 * 100 if time1 > 0 else float('inf')
                print(f"Diferencia: {diff_ms:.2f} ms ({diff_percent:.2f}%)")
            print()
        
        # Cantidad de resultados
        if self.metrics.get('result_count'):
            print("CANTIDAD DE RESULTADOS:")
            for method, count in self.metrics['result_count'].items():
                print(f"{method.upper()}: {count} resultados")
            print()
        
        # Solapamiento de resultados
        if self.metrics.get('overlap'):
            print("SOLAPAMIENTO DE RESULTADOS:")
            for comparison, data in self.metrics['overlap'].items():
                method1, method2 = comparison.split('_vs_')
                print(f"Resultados comunes: {data['common_count']}")
                print(f"Porcentaje de overlap: {data['percentage']:.2f}%")
                if 'avg_position_diff' in data:
                    print(f"Diferencia promedio de posición: {data['avg_position_diff']:.2f}")
            print()
        
        # Coincidencia de resultado principal
        if self.metrics.get('top_result_match'):
            print("COMPARACIÓN DE RESULTADOS PRINCIPALES:")
            for comparison, match in self.metrics['top_result_match'].items():
                method1, method2 = comparison.split('_vs_')
                print(f"Mismo resultado principal: {'Sí' if match else 'No'}")
            print()
            
            # Mostrar textos de resultados principales
            methods = list(self.systems.keys())
            if len(methods) >= 2:
                method1, method2 = methods[0], methods[1]
                
                if ('results' in self.results[method1] and self.results[method1]['results'] and 
                    'results' in self.results[method2] and self.results[method2]['results']):
                    
                    result1 = self.results[method1]['results'][0]
                    result2 = self.results[method2]['results'][0]
                    
                    text1 = self._extract_text(result1)
                    text2 = self._extract_text(result2)
                    
                    print(f"{method1.upper()} TOP RESULT:")
                    print(f"{text1[:100]}...\n")
                    
                    print(f"{method2.upper()} TOP RESULT:")
                    print(f"{text2[:100]}...\n")
        
        # Resultados únicos
        if self.metrics.get('unique_results'):
            print("RESULTADOS ÚNICOS:")
            for key, count in self.metrics['unique_results'].items():
                method = key.replace('unique_to_', '')
                print(f"Solo en {method.upper()}: {count}")
            print()
        
        print("=" * 50)
        print(f"Resultados completos guardados en: data/evaluation/benchmark_results/comparison_reports")
        print("=" * 50 + "\n")
    
    def _extract_text(self, result: Dict[str, Any]) -> str:
        """
        Extrae el texto de un resultado.
        
        Args:
            result: Resultado de búsqueda
            
        Returns:
            Texto extraído del resultado
        """
        if isinstance(result, dict):
            # Intentar diferentes claves para el texto
            for key in ['texto', 'text', 'content', 'chunk']:
                if key in result and isinstance(result[key], str):
                    return result[key]
            
            # Si no se encontró ninguna clave conocida, devolver la representación del diccionario
            return str(result)
        else:
            return str(result)


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description='Comparar sistemas de búsqueda')
    parser.add_argument('--methods', type=str, default='tfidf,bm25',
                        help='Métodos a comparar, separados por comas (tfidf,bm25,transformers,hybrid,all)')
    parser.add_argument('--query', type=str, required=True,
                        help='Consulta a buscar')
    parser.add_argument('--top_k', type=int, default=5,
                        help='Número de resultados a recuperar')
    parser.add_argument('--comprehensive', action='store_true',
                        help='Realizar evaluación exhaustiva con métricas adicionales')
    parser.add_argument('--output_format', type=str, default='console',
                        choices=['console', 'json', 'csv'],
                        help='Formato de salida de resultados')
    
    args = parser.parse_args()
    
    # Convertir métodos a lista
    methods = args.methods.split(',')
    if 'all' in methods:
        methods = ['tfidf', 'bm25', 'transformers', 'hybrid']
    
    # Crear comparador
    comparator = SystemComparator(methods, args.top_k, args.comprehensive)
    
    # Ejecutar comparación
    report = comparator.compare(args.query)
    
    # Mostrar resultados
    if args.output_format == 'console':
        comparator.print_summary(args.query)
    elif args.output_format == 'json':
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.output_format == 'csv':
        # TODO: Implementar salida en formato CSV
        print("Formato CSV no implementado aún")


if __name__ == '__main__':
    main()
