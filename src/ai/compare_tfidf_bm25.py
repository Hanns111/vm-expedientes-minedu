#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comparador de sistemas TF-IDF vs BM25 para búsqueda en documentos normativos.
Este script permite ejecutar la misma consulta en ambos sistemas y comparar resultados.

Uso:
    python compare_tfidf_bm25.py --query "consulta de ejemplo" --top_k 5
"""

import os
import json
import pickle
import logging
import time
import argparse
import sys
from datetime import datetime
from typing import Dict, List, Any, Tuple, Set

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/compare_systems.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SystemComparator")

# Asegurar que existe el directorio de logs
os.makedirs("logs", exist_ok=True)

class SystemComparator:
    """Comparador de sistemas de búsqueda TF-IDF vs BM25."""
    
    def __init__(self, tfidf_vectorstore_path: str, bm25_vectorstore_path: str):
        """
        Inicializa el comparador de sistemas.
        
        Args:
            tfidf_vectorstore_path: Ruta al vectorstore TF-IDF
            bm25_vectorstore_path: Ruta al vectorstore BM25
        """
        self.tfidf_vectorstore_path = tfidf_vectorstore_path
        self.bm25_vectorstore_path = bm25_vectorstore_path
        self.tfidf_system = None
        self.bm25_system = None
        self.output_dir = "data/evaluation/benchmark_results/comparison_reports"
        
        # Asegurar que existe el directorio de salida
        os.makedirs(self.output_dir, exist_ok=True)
    
    def load_systems(self):
        """Carga los sistemas de búsqueda."""
        try:
            logger.info("Cargando sistemas de búsqueda...")
            
            # Importar dinámicamente para evitar dependencias circulares
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            
            # Cargar sistema TF-IDF existente
            from search_vectorstore_hybrid import SearchVectorstore
            self.tfidf_system = SearchVectorstore(self.tfidf_vectorstore_path)
            
            # Cargar sistema BM25
            from search_vectorstore_bm25 import BM25Search
            self.bm25_system = BM25Search(self.bm25_vectorstore_path)
            
            logger.info("Sistemas de búsqueda cargados correctamente")
        except Exception as e:
            logger.error(f"Error al cargar sistemas: {str(e)}")
            raise
    
    def compare_search(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Compara los resultados de búsqueda entre TF-IDF y BM25.
        
        Args:
            query: Consulta a ejecutar
            top_k: Número de resultados a considerar
            
        Returns:
            Diccionario con resultados comparativos
        """
        try:
            logger.info(f"Comparando sistemas para consulta: '{query}'")
            results = {
                "query": query,
                "top_k": top_k,
                "timestamp": datetime.now().isoformat(),
                "systems": {},
                "metrics": {},
                "analysis": {}
            }
            
            # Ejecutar búsqueda en TF-IDF
            start_time = time.time()
            tfidf_response = self.tfidf_system.search(query, top_k)
            tfidf_time = time.time() - start_time
            
            # Ejecutar búsqueda en BM25
            start_time = time.time()
            bm25_response = self.bm25_system.generate_response(query, top_k)
            bm25_time = time.time() - start_time
            
            # Almacenar resultados
            results["systems"]["tfidf"] = {
                "results": tfidf_response.get("results", []),
                "time": tfidf_time
            }
            
            results["systems"]["bm25"] = {
                "results": bm25_response.get("results", []),
                "time": bm25_time
            }
            
            # Calcular métricas comparativas
            results["metrics"] = self._calculate_metrics(
                tfidf_response.get("results", []),
                bm25_response.get("results", []),
                tfidf_time,
                bm25_time
            )
            
            # Análisis cualitativo
            results["analysis"] = self._analyze_results(
                tfidf_response.get("results", []),
                bm25_response.get("results", [])
            )
            
            return results
        except Exception as e:
            logger.error(f"Error al comparar sistemas: {str(e)}")
            return {
                "query": query,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _calculate_metrics(
        self, 
        tfidf_results: List[Dict[str, Any]], 
        bm25_results: List[Dict[str, Any]],
        tfidf_time: float,
        bm25_time: float
    ) -> Dict[str, Any]:
        """
        Calcula métricas comparativas entre los resultados.
        
        Args:
            tfidf_results: Resultados de TF-IDF
            bm25_results: Resultados de BM25
            tfidf_time: Tiempo de ejecución de TF-IDF
            bm25_time: Tiempo de ejecución de BM25
            
        Returns:
            Diccionario con métricas comparativas
        """
        # Extraer IDs de chunks para comparación
        tfidf_ids = [r.get("id", r.get("chunk_id", "")) for r in tfidf_results]
        bm25_ids = [r.get("id", r.get("chunk_id", "")) for r in bm25_results]
        
        # Calcular overlap (intersección de resultados)
        common_ids = set(tfidf_ids) & set(bm25_ids)
        overlap_percentage = len(common_ids) / max(len(tfidf_ids), len(bm25_ids)) * 100 if max(len(tfidf_ids), len(bm25_ids)) > 0 else 0
        
        # Calcular posiciones de resultados comunes
        position_diff = 0
        position_count = 0
        
        for chunk_id in common_ids:
            tfidf_pos = tfidf_ids.index(chunk_id)
            bm25_pos = bm25_ids.index(chunk_id)
            position_diff += abs(tfidf_pos - bm25_pos)
            position_count += 1
        
        avg_position_diff = position_diff / position_count if position_count > 0 else 0
        
        # Calcular promedio de scores (normalizado)
        tfidf_avg_score = sum([r.get("score", 0) for r in tfidf_results]) / len(tfidf_results) if tfidf_results else 0
        bm25_avg_score = sum([r.get("score", 0) for r in bm25_results]) / len(bm25_results) if bm25_results else 0
        
        # Comparación de tiempo
        time_diff_percentage = (tfidf_time - bm25_time) / tfidf_time * 100 if tfidf_time > 0 else 0
        
        return {
            "result_count": {
                "tfidf": len(tfidf_results),
                "bm25": len(bm25_results),
                "difference": len(bm25_results) - len(tfidf_results)
            },
            "overlap": {
                "common_results": len(common_ids),
                "percentage": overlap_percentage,
                "avg_position_difference": avg_position_diff
            },
            "scores": {
                "tfidf_avg": tfidf_avg_score,
                "bm25_avg": bm25_avg_score
            },
            "time_performance": {
                "tfidf_time": tfidf_time,
                "bm25_time": bm25_time,
                "difference_ms": (tfidf_time - bm25_time) * 1000,
                "percentage_improvement": time_diff_percentage
            }
        }
    
    def _analyze_results(
        self, 
        tfidf_results: List[Dict[str, Any]], 
        bm25_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Realiza un análisis cualitativo de los resultados.
        
        Args:
            tfidf_results: Resultados de TF-IDF
            bm25_results: Resultados de BM25
            
        Returns:
            Diccionario con análisis cualitativo
        """
        # Identificar resultados únicos en cada sistema
        tfidf_ids = set([r.get("id", r.get("chunk_id", "")) for r in tfidf_results])
        bm25_ids = set([r.get("id", r.get("chunk_id", "")) for r in bm25_results])
        
        unique_to_tfidf = tfidf_ids - bm25_ids
        unique_to_bm25 = bm25_ids - tfidf_ids
        
        # Extraer los resultados únicos completos
        unique_tfidf_results = [r for r in tfidf_results if r.get("id", r.get("chunk_id", "")) in unique_to_tfidf]
        unique_bm25_results = [r for r in bm25_results if r.get("id", r.get("chunk_id", "")) in unique_to_bm25]
        
        # Análisis de longitud de texto en resultados (compatible con 'text' o 'texto')
        tfidf_avg_length = sum([len(r.get("texto", r.get("text", ""))) for r in tfidf_results]) / len(tfidf_results) if tfidf_results else 0
        bm25_avg_length = sum([len(r.get("texto", r.get("text", ""))) for r in bm25_results]) / len(bm25_results) if bm25_results else 0
        
        return {
            "unique_results": {
                "tfidf_only": len(unique_to_tfidf),
                "bm25_only": len(unique_to_bm25)
            },
            "content_analysis": {
                "tfidf_avg_length": tfidf_avg_length,
                "bm25_avg_length": bm25_avg_length,
                "length_difference": bm25_avg_length - tfidf_avg_length
            },
            "top_result_comparison": {
                "tfidf_top": tfidf_results[0].get("texto", tfidf_results[0].get("text", ""))[:150] + "..." if tfidf_results else "No results",
                "bm25_top": bm25_results[0].get("texto", bm25_results[0].get("text", ""))[:150] + "..." if bm25_results else "No results",
                "same_top_result": (tfidf_results[0].get("id", "") == bm25_results[0].get("id", "")) if tfidf_results and bm25_results else False
            }
        }
    
    def save_comparison_results(self, results: Dict[str, Any], output_format: str = "json") -> str:
        """
        Guarda los resultados de la comparación en un archivo.
        
        Args:
            results: Resultados de la comparación
            output_format: Formato de salida (json, csv)
            
        Returns:
            Ruta al archivo guardado
        """
        try:
            # Generar nombre de archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            query_slug = results["query"].lower().replace(" ", "_")[:30]
            filename = f"compare_tfidf_bm25_{query_slug}_{timestamp}"
            
            if output_format == "json":
                output_path = os.path.join(self.output_dir, f"{filename}.json")
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
            else:
                # Implementar otros formatos si es necesario
                output_path = os.path.join(self.output_dir, f"{filename}.json")
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Resultados guardados en: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error al guardar resultados: {str(e)}")
            return ""
    
    def print_comparison_summary(self, results: Dict[str, Any]) -> None:
        """
        Imprime un resumen de la comparación en consola.
        
        Args:
            results: Resultados de la comparación
        """
        try:
            print("\n" + "="*50)
            print(f"COMPARACIÓN TF-IDF vs BM25: '{results['query']}'")
            print("="*50)
            
            # Métricas de tiempo
            time_metrics = results["metrics"]["time_performance"]
            print("\nTIEMPO DE EJECUCIÓN:")
            print(f"TF-IDF: {time_metrics['tfidf_time']:.4f} segundos")
            print(f"BM25:   {time_metrics['bm25_time']:.4f} segundos")
            print(f"Diferencia: {time_metrics['difference_ms']:.2f} ms ({time_metrics['percentage_improvement']:.2f}%)")
            
            # Métricas de resultados
            result_metrics = results["metrics"]["result_count"]
            print("\nCANTIDAD DE RESULTADOS:")
            print(f"TF-IDF: {result_metrics['tfidf']} resultados")
            print(f"BM25:   {result_metrics['bm25']} resultados")
            
            # Overlap
            overlap = results["metrics"]["overlap"]
            print("\nSOLAPAMIENTO DE RESULTADOS:")
            print(f"Resultados comunes: {overlap['common_results']}")
            print(f"Porcentaje de overlap: {overlap['percentage']:.2f}%")
            print(f"Diferencia promedio de posición: {overlap['avg_position_difference']:.2f}")
            
            # Top resultados
            top_comparison = results["analysis"]["top_result_comparison"]
            print("\nCOMPARACIÓN DE RESULTADOS PRINCIPALES:")
            print(f"Mismo resultado principal: {'Sí' if top_comparison['same_top_result'] else 'No'}")
            print("\nTF-IDF TOP RESULT:")
            print(f"{top_comparison['tfidf_top']}")
            print("\nBM25 TOP RESULT:")
            print(f"{top_comparison['bm25_top']}")
            
            # Resultados únicos
            unique = results["analysis"]["unique_results"]
            print("\nRESULTADOS ÚNICOS:")
            print(f"Solo en TF-IDF: {unique['tfidf_only']}")
            print(f"Solo en BM25: {unique['bm25_only']}")
            
            print("\n" + "="*50)
            print(f"Resultados completos guardados en: {self.output_dir}")
            print("="*50 + "\n")
        except Exception as e:
            logger.error(f"Error al imprimir resumen: {str(e)}")
            print(f"Error al generar resumen: {str(e)}")

def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description="Comparador de sistemas TF-IDF vs BM25")
    parser.add_argument("--query", type=str, required=True, help="Consulta a ejecutar")
    parser.add_argument("--top_k", type=int, default=5, help="Número de resultados a considerar")
    parser.add_argument("--output", type=str, default="json", choices=["json", "csv"], help="Formato de salida")
    
    args = parser.parse_args()
    
    try:
        # Rutas a los vectorstores
        tfidf_vectorstore_path = "data/processed/vectorstore_semantic_full_v2.pkl"
        bm25_vectorstore_path = "data/processed/vectorstore_bm25_test.pkl"
        
        # Crear comparador
        comparator = SystemComparator(tfidf_vectorstore_path, bm25_vectorstore_path)
        
        # Cargar sistemas
        comparator.load_systems()
        
        # Ejecutar comparación
        results = comparator.compare_search(args.query, args.top_k)
        
        # Guardar resultados
        output_path = comparator.save_comparison_results(results, args.output)
        
        # Imprimir resumen
        comparator.print_comparison_summary(results)
        
    except Exception as e:
        logger.error(f"Error en la función principal: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
