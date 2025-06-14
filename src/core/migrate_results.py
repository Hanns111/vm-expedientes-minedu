#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de Migración de Resultados a Base de Datos SQLite

Este script migra los resultados existentes de archivos JSON a la nueva
base de datos centralizada de experimentos.

Autor: Hanns
Fecha: 2025-06-14
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.experiment_database import ExperimentDatabase

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MigrateResults')


class ResultsMigrator:
    """
    Migrador de resultados de archivos JSON a base de datos SQLite.
    """
    
    def __init__(self, db_path: str = "data/evaluation/experimentos.db"):
        """
        Inicializar migrador.
        
        Args:
            db_path: Ruta a la base de datos SQLite
        """
        self.db = ExperimentDatabase(db_path)
        self.migrated_count = 0
        self.error_count = 0
    
    def find_json_results(self, base_path: str = "data/evaluation") -> List[Path]:
        """
        Encontrar archivos JSON con resultados de experimentos.
        
        Args:
            base_path: Directorio base para buscar archivos
            
        Returns:
            Lista de rutas a archivos JSON
        """
        base_dir = Path(base_path)
        json_files = []
        
        if base_dir.exists():
            # Buscar archivos JSON en el directorio y subdirectorios
            for pattern in ["*.json", "**/*.json"]:
                json_files.extend(base_dir.glob(pattern))
        
        # Filtrar archivos que parecen ser resultados de experimentos
        experiment_files = []
        for file_path in json_files:
            if any(keyword in file_path.name.lower() for keyword in [
                "result", "evaluation", "experiment", "test", "comparison",
                "hybrid", "bm25", "tfidf", "transformer"
            ]):
                experiment_files.append(file_path)
        
        logger.info(f"Encontrados {len(experiment_files)} archivos de resultados")
        return experiment_files
    
    def parse_experiment_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parsear archivo de resultados de experimento.
        
        Args:
            file_path: Ruta al archivo JSON
            
        Returns:
            Datos del experimento parseados o None si hay error
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Determinar tipo de experimento basado en el contenido
            experiment_info = self._extract_experiment_info(data, file_path)
            
            return {
                "file_path": file_path,
                "data": data,
                "experiment_info": experiment_info
            }
            
        except Exception as e:
            logger.error(f"Error parseando {file_path}: {e}")
            return None
    
    def _extract_experiment_info(self, data: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
        """
        Extraer información del experimento del archivo.
        
        Args:
            data: Datos del archivo JSON
            file_path: Ruta del archivo
            
        Returns:
            Información del experimento
        """
        # Intentar extraer información del nombre del archivo
        filename = file_path.stem.lower()
        
        # Determinar modelo basado en el nombre del archivo
        if "hybrid" in filename:
            modelo = "Hybrid"
        elif "bm25" in filename:
            modelo = "BM25"
        elif "tfidf" in filename:
            modelo = "TF-IDF"
        elif "transformer" in filename:
            modelo = "Transformers"
        else:
            modelo = "Unknown"
        
        # Extraer información del contenido si está disponible
        if isinstance(data, dict):
            if "experiment" in data:
                exp_data = data["experiment"]
                nombre = exp_data.get("name", f"Experimento {modelo}")
                descripcion = exp_data.get("description", f"Experimento con {modelo}")
            elif "metadata" in data:
                metadata = data["metadata"]
                nombre = metadata.get("experiment_name", f"Experimento {modelo}")
                descripcion = metadata.get("description", f"Experimento con {modelo}")
            else:
                nombre = f"Experimento {modelo} - {file_path.stem}"
                descripcion = f"Resultados de experimento con {modelo}"
        else:
            nombre = f"Experimento {modelo} - {file_path.stem}"
            descripcion = f"Resultados de experimento con {modelo}"
        
        return {
            "nombre": nombre,
            "modelo": modelo,
            "descripcion": descripcion,
            "timestamp": file_path.stat().st_mtime
        }
    
    def migrate_experiment(self, experiment_data: Dict[str, Any]) -> bool:
        """
        Migrar un experimento a la base de datos.
        
        Args:
            experiment_data: Datos del experimento parseados
            
        Returns:
            True si la migración fue exitosa
        """
        try:
            file_path = experiment_data["file_path"]
            data = experiment_data["data"]
            exp_info = experiment_data["experiment_info"]
            
            logger.info(f"Migrando experimento: {exp_info['nombre']}")
            
            # Crear experimento en la base de datos
            experiment_id = self.db.create_experiment(
                nombre=exp_info["nombre"],
                modelo=exp_info["modelo"],
                descripcion=exp_info["descripcion"],
                configuracion={"source_file": str(file_path)}
            )
            
            # Procesar consultas y resultados
            queries_processed = self._process_queries_and_results(data, experiment_id)
            
            if queries_processed > 0:
                # Finalizar experimento
                self.db.finish_experiment(experiment_id, "migrado")
                self.migrated_count += 1
                logger.info(f"Experimento migrado exitosamente: {queries_processed} consultas")
                return True
            else:
                # Si no hay consultas, eliminar el experimento
                logger.warning(f"No se encontraron consultas en {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error migrando experimento: {e}")
            self.error_count += 1
            return False
    
    def _process_queries_and_results(self, data: Any, experiment_id: int) -> int:
        """
        Procesar consultas y resultados del experimento.
        
        Args:
            data: Datos del experimento
            experiment_id: ID del experimento
            
        Returns:
            Número de consultas procesadas
        """
        queries_processed = 0
        
        # Diferentes formatos de datos
        if isinstance(data, dict):
            # Formato con consultas explícitas
            if "queries" in data:
                queries = data["queries"]
                for query_data in queries:
                    if self._process_single_query(query_data, experiment_id):
                        queries_processed += 1
            
            # Formato con resultados directos
            elif "results" in data:
                results = data["results"]
                if isinstance(results, list):
                    # Asumir que es una lista de consultas
                    for query_result in results:
                        if self._process_single_query(query_result, experiment_id):
                            queries_processed += 1
            
            # Formato con métricas globales
            elif "metrics" in data:
                # Crear una consulta sintética con métricas globales
                query_data = {
                    "query": "Métricas globales del experimento",
                    "results": [],
                    "metrics": data["metrics"]
                }
                if self._process_single_query(query_data, experiment_id):
                    queries_processed += 1
        
        elif isinstance(data, list):
            # Lista de resultados
            for item in data:
                if self._process_single_query(item, experiment_id):
                    queries_processed += 1
        
        return queries_processed
    
    def _process_single_query(self, query_data: Any, experiment_id: int) -> bool:
        """
        Procesar una sola consulta y sus resultados.
        
        Args:
            query_data: Datos de la consulta
            experiment_id: ID del experimento
            
        Returns:
            True si se procesó exitosamente
        """
        try:
            # Extraer información de la consulta
            if isinstance(query_data, dict):
                query_text = query_data.get("query", "Consulta sin texto")
                results = query_data.get("results", [])
                metrics = query_data.get("metrics", {})
                execution_time = query_data.get("execution_time", 0.0)
            else:
                # Si no es un dict, asumir que es el texto de la consulta
                query_text = str(query_data)
                results = []
                metrics = {}
                execution_time = 0.0
            
            # Agregar consulta
            query_id = self.db.add_query(
                experiment_id=experiment_id,
                query=query_text,
                categoria="migrado",
                dificultad="media"
            )
            
            # Agregar resultados si existen
            if results:
                self.db.add_results(query_id, experiment_id, results, execution_time)
            
            # Agregar métricas si existen
            if metrics:
                self.db.add_metrics(query_id, experiment_id, metrics)
            
            return True
            
        except Exception as e:
            logger.error(f"Error procesando consulta: {e}")
            return False
    
    def migrate_all_results(self, base_path: str = "data/evaluation") -> Dict[str, int]:
        """
        Migrar todos los resultados encontrados.
        
        Args:
            base_path: Directorio base para buscar archivos
            
        Returns:
            Estadísticas de migración
        """
        logger.info("Iniciando migración de resultados...")
        
        # Encontrar archivos
        json_files = self.find_json_results(base_path)
        
        if not json_files:
            logger.warning("No se encontraron archivos de resultados para migrar")
            return {"migrated": 0, "errors": 0, "total": 0}
        
        # Procesar cada archivo
        for file_path in json_files:
            logger.info(f"Procesando: {file_path}")
            
            experiment_data = self.parse_experiment_file(file_path)
            if experiment_data:
                self.migrate_experiment(experiment_data)
        
        # Estadísticas finales
        stats = {
            "migrated": self.migrated_count,
            "errors": self.error_count,
            "total": len(json_files)
        }
        
        logger.info(f"Migración completada: {stats['migrated']} exitosas, {stats['errors']} errores")
        return stats
    
    def generate_migration_report(self, stats: Dict[str, int], output_path: str = "data/evaluation/migration_report.json"):
        """
        Generar reporte de migración.
        
        Args:
            stats: Estadísticas de migración
            output_path: Ruta del archivo de reporte
        """
        report = {
            "migration_date": str(Path().cwd()),
            "statistics": stats,
            "database_path": self.db.db_path,
            "summary": {
                "total_files_found": stats["total"],
                "successfully_migrated": stats["migrated"],
                "failed_migrations": stats["errors"],
                "success_rate": f"{(stats['migrated'] / stats['total'] * 100):.1f}%" if stats["total"] > 0 else "0%"
            }
        }
        
        # Asegurar directorio de salida
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Guardar reporte
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Reporte de migración guardado en: {output_path}")


def main():
    """Función principal del script de migración"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrar resultados de experimentos a base de datos SQLite")
    parser.add_argument("--base-path", default="data/evaluation", help="Directorio base para buscar archivos")
    parser.add_argument("--db-path", default="data/evaluation/experimentos.db", help="Ruta de la base de datos")
    parser.add_argument("--report-path", default="data/evaluation/migration_report.json", help="Ruta del reporte")
    
    args = parser.parse_args()
    
    # Crear migrador
    migrator = ResultsMigrator(args.db_path)
    
    # Ejecutar migración
    stats = migrator.migrate_all_results(args.base_path)
    
    # Generar reporte
    migrator.generate_migration_report(stats, args.report_path)
    
    # Mostrar resumen
    print("\n" + "="*50)
    print("RESUMEN DE MIGRACIÓN")
    print("="*50)
    print(f"Archivos encontrados: {stats['total']}")
    print(f"Migraciones exitosas: {stats['migrated']}")
    print(f"Errores: {stats['errors']}")
    print(f"Tasa de éxito: {(stats['migrated'] / stats['total'] * 100):.1f}%" if stats["total"] > 0 else "0%")
    print(f"Base de datos: {args.db_path}")
    print("="*50)


if __name__ == "__main__":
    main() 