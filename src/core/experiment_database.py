#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistema de Base de Datos para Experimentos del Sistema RAG MINEDU

Este módulo implementa una base de datos SQLite para almacenar y gestionar
los resultados de experimentos de manera centralizada.

Autor: Hanns
Fecha: 2025-06-14
"""

import sqlite3
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ExperimentDatabase')


class ExperimentDatabase:
    """
    Sistema de base de datos para experimentos del sistema RAG MINEDU.
    
    Gestiona:
    - Experimentos y sus metadatos
    - Resultados de búsquedas
    - Métricas de evaluación
    - Configuraciones de experimentos
    """
    
    def __init__(self, db_path: str = "data/evaluation/experimentos.db"):
        """
        Inicializa la base de datos de experimentos.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = db_path
        self._ensure_db_directory()
        self._create_tables()
        logger.info(f"Base de datos de experimentos inicializada: {db_path}")
    
    def _ensure_db_directory(self):
        """Asegurar que el directorio de la base de datos existe"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def _create_tables(self):
        """Crear las tablas de la base de datos"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabla de experimentos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS experimentos (
                    id_experimento INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    descripcion TEXT,
                    modelo TEXT NOT NULL,
                    configuracion TEXT,
                    timestamp_inicio DATETIME DEFAULT CURRENT_TIMESTAMP,
                    timestamp_fin DATETIME,
                    estado TEXT DEFAULT 'en_progreso',
                    usuario TEXT,
                    version_sistema TEXT,
                    UNIQUE(nombre, timestamp_inicio)
                )
            ''')
            
            # Tabla de consultas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS consultas (
                    id_consulta INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_experimento INTEGER,
                    query TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    categoria TEXT,
                    dificultad TEXT,
                    FOREIGN KEY (id_experimento) REFERENCES experimentos (id_experimento)
                )
            ''')
            
            # Tabla de resultados
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS resultados (
                    id_resultado INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_consulta INTEGER,
                    id_experimento INTEGER,
                    documento_id TEXT,
                    texto TEXT,
                    score REAL,
                    rank INTEGER,
                    metodo TEXT,
                    tiempo_ejecucion REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (id_consulta) REFERENCES consultas (id_consulta),
                    FOREIGN KEY (id_experimento) REFERENCES experimentos (id_experimento)
                )
            ''')
            
            # Tabla de métricas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metricas (
                    id_metrica INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_consulta INTEGER,
                    id_experimento INTEGER,
                    nombre_metrica TEXT NOT NULL,
                    valor REAL,
                    detalles TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (id_consulta) REFERENCES consultas (id_consulta),
                    FOREIGN KEY (id_experimento) REFERENCES experimentos (id_experimento)
                )
            ''')
            
            # Tabla de configuraciones
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS configuraciones (
                    id_configuracion INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_experimento INTEGER,
                    parametro TEXT NOT NULL,
                    valor TEXT,
                    tipo TEXT,
                    descripcion TEXT,
                    FOREIGN KEY (id_experimento) REFERENCES experimentos (id_experimento)
                )
            ''')
            
            conn.commit()
            logger.info("Tablas de base de datos creadas/verificadas")
    
    def create_experiment(
        self,
        nombre: str,
        modelo: str,
        descripcion: str = "",
        configuracion: Optional[Dict[str, Any]] = None,
        usuario: str = "sistema"
    ) -> int:
        """
        Crear un nuevo experimento.
        
        Args:
            nombre: Nombre del experimento
            modelo: Modelo utilizado (TF-IDF, BM25, Transformers, Hybrid)
            descripcion: Descripción del experimento
            configuracion: Configuración del experimento
            usuario: Usuario que ejecuta el experimento
            
        Returns:
            ID del experimento creado
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            config_json = json.dumps(configuracion) if configuracion else None
            
            cursor.execute('''
                INSERT INTO experimentos (nombre, descripcion, modelo, configuracion, usuario, version_sistema)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (nombre, descripcion, modelo, config_json, usuario, "v1.3.0"))
            
            experiment_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"Experimento creado: {nombre} (ID: {experiment_id})")
            return experiment_id
    
    def add_query(
        self,
        experiment_id: int,
        query: str,
        categoria: str = "general",
        dificultad: str = "media"
    ) -> int:
        """
        Agregar una consulta al experimento.
        
        Args:
            experiment_id: ID del experimento
            query: Consulta de búsqueda
            categoria: Categoría de la consulta
            dificultad: Dificultad de la consulta
            
        Returns:
            ID de la consulta creada
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO consultas (id_experimento, query, categoria, dificultad)
                VALUES (?, ?, ?, ?)
            ''', (experiment_id, query, categoria, dificultad))
            
            query_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"Consulta agregada al experimento {experiment_id}: {query[:50]}...")
            return query_id
    
    def add_results(
        self,
        query_id: int,
        experiment_id: int,
        results: List[Dict[str, Any]],
        execution_time: float
    ):
        """
        Agregar resultados de búsqueda.
        
        Args:
            query_id: ID de la consulta
            experiment_id: ID del experimento
            results: Lista de resultados de búsqueda
            execution_time: Tiempo de ejecución
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for rank, result in enumerate(results, 1):
                cursor.execute('''
                    INSERT INTO resultados (
                        id_consulta, id_experimento, documento_id, texto, 
                        score, rank, metodo, tiempo_ejecucion
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    query_id, experiment_id,
                    result.get('id', f"doc_{rank}"),
                    result.get('text', '')[:1000],  # Limitar longitud
                    result.get('score', 0.0),
                    rank,
                    result.get('method', 'unknown'),
                    execution_time
                ))
            
            conn.commit()
            logger.info(f"Resultados agregados para consulta {query_id}: {len(results)} documentos")
    
    def add_metrics(
        self,
        query_id: int,
        experiment_id: int,
        metrics: Dict[str, Any]
    ):
        """
        Agregar métricas de evaluación.
        
        Args:
            query_id: ID de la consulta
            experiment_id: ID del experimento
            metrics: Diccionario de métricas
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for metric_name, metric_value in metrics.items():
                if isinstance(metric_value, (int, float)):
                    cursor.execute('''
                        INSERT INTO metricas (id_consulta, id_experimento, nombre_metrica, valor)
                        VALUES (?, ?, ?, ?)
                    ''', (query_id, experiment_id, metric_name, metric_value))
                else:
                    # Para métricas complejas, guardar como JSON
                    cursor.execute('''
                        INSERT INTO metricas (id_consulta, id_experimento, nombre_metrica, valor, detalles)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (query_id, experiment_id, metric_name, None, json.dumps(metric_value)))
            
            conn.commit()
            logger.info(f"Métricas agregadas para consulta {query_id}: {len(metrics)} métricas")
    
    def finish_experiment(self, experiment_id: int, estado: str = "completado"):
        """
        Finalizar un experimento.
        
        Args:
            experiment_id: ID del experimento
            estado: Estado final del experimento
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE experimentos 
                SET estado = ?, timestamp_fin = CURRENT_TIMESTAMP
                WHERE id_experimento = ?
            ''', (estado, experiment_id))
            
            conn.commit()
            logger.info(f"Experimento {experiment_id} finalizado con estado: {estado}")
    
    def get_experiment_results(self, experiment_id: int) -> Dict[str, Any]:
        """
        Obtener resultados completos de un experimento.
        
        Args:
            experiment_id: ID del experimento
            
        Returns:
            Diccionario con todos los resultados del experimento
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Obtener información del experimento
            cursor.execute('''
                SELECT nombre, descripcion, modelo, timestamp_inicio, timestamp_fin, estado
                FROM experimentos WHERE id_experimento = ?
            ''', (experiment_id,))
            
            exp_info = cursor.fetchone()
            if not exp_info:
                return {"error": "Experimento no encontrado"}
            
            # Obtener consultas y resultados
            cursor.execute('''
                SELECT c.id_consulta, c.query, c.categoria, c.dificultad, c.timestamp,
                       COUNT(r.id_resultado) as num_resultados,
                       AVG(r.tiempo_ejecucion) as tiempo_promedio
                FROM consultas c
                LEFT JOIN resultados r ON c.id_consulta = r.id_consulta
                WHERE c.id_experimento = ?
                GROUP BY c.id_consulta
                ORDER BY c.timestamp
            ''', (experiment_id,))
            
            queries = []
            for row in cursor.fetchall():
                query_data = {
                    "id_consulta": row[0],
                    "query": row[1],
                    "categoria": row[2],
                    "dificultad": row[3],
                    "timestamp": row[4],
                    "num_resultados": row[5],
                    "tiempo_promedio": row[6]
                }
                
                # Obtener resultados específicos de esta consulta
                cursor.execute('''
                    SELECT documento_id, texto, score, rank, metodo
                    FROM resultados
                    WHERE id_consulta = ?
                    ORDER BY rank
                ''', (row[0],))
                
                query_data["resultados"] = [
                    {
                        "documento_id": r[0],
                        "texto": r[1],
                        "score": r[2],
                        "rank": r[3],
                        "metodo": r[4]
                    }
                    for r in cursor.fetchall()
                ]
                
                # Obtener métricas de esta consulta
                cursor.execute('''
                    SELECT nombre_metrica, valor, detalles
                    FROM metricas
                    WHERE id_consulta = ?
                ''', (row[0],))
                
                query_data["metricas"] = {}
                for metric_row in cursor.fetchall():
                    metric_name = metric_row[0]
                    metric_value = metric_row[1]
                    metric_details = metric_row[2]
                    
                    if metric_details:
                        try:
                            metric_value = json.loads(metric_details)
                        except:
                            pass
                    
                    query_data["metricas"][metric_name] = metric_value
                
                queries.append(query_data)
            
            return {
                "experimento": {
                    "id": experiment_id,
                    "nombre": exp_info[0],
                    "descripcion": exp_info[1],
                    "modelo": exp_info[2],
                    "timestamp_inicio": exp_info[3],
                    "timestamp_fin": exp_info[4],
                    "estado": exp_info[5]
                },
                "consultas": queries,
                "resumen": {
                    "total_consultas": len(queries),
                    "total_resultados": sum(q["num_resultados"] for q in queries),
                    "tiempo_promedio_total": sum(q["tiempo_promedio"] or 0 for q in queries) / len(queries) if queries else 0
                }
            }
    
    def get_experiments_summary(self) -> List[Dict[str, Any]]:
        """
        Obtener resumen de todos los experimentos.
        
        Returns:
            Lista de resúmenes de experimentos
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT e.id_experimento, e.nombre, e.modelo, e.estado, 
                       e.timestamp_inicio, e.timestamp_fin,
                       COUNT(DISTINCT c.id_consulta) as num_consultas,
                       COUNT(r.id_resultado) as num_resultados
                FROM experimentos e
                LEFT JOIN consultas c ON e.id_experimento = c.id_experimento
                LEFT JOIN resultados r ON c.id_consulta = r.id_consulta
                GROUP BY e.id_experimento
                ORDER BY e.timestamp_inicio DESC
            ''')
            
            return [
                {
                    "id": row[0],
                    "nombre": row[1],
                    "modelo": row[2],
                    "estado": row[3],
                    "timestamp_inicio": row[4],
                    "timestamp_fin": row[5],
                    "num_consultas": row[6],
                    "num_resultados": row[7]
                }
                for row in cursor.fetchall()
            ]
    
    def export_experiment_to_json(self, experiment_id: int, output_path: str):
        """
        Exportar experimento a archivo JSON.
        
        Args:
            experiment_id: ID del experimento
            output_path: Ruta del archivo de salida
        """
        results = self.get_experiment_results(experiment_id)
        
        if "error" in results:
            logger.error(f"Error exportando experimento: {results['error']}")
            return
        
        # Asegurar directorio de salida
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Exportar a JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Experimento {experiment_id} exportado a: {output_path}")


# Función de utilidad para crear la base de datos
def create_experiment_database(db_path: str = "data/evaluation/experimentos.db") -> ExperimentDatabase:
    """
    Crear y configurar la base de datos de experimentos.
    
    Args:
        db_path: Ruta al archivo de base de datos
        
    Returns:
        Instancia de ExperimentDatabase configurada
    """
    return ExperimentDatabase(db_path)


# Ejemplo de uso
if __name__ == "__main__":
    # Crear base de datos
    db = create_experiment_database()
    
    # Crear experimento de prueba
    experiment_id = db.create_experiment(
        nombre="Test TF-IDF vs BM25",
        modelo="TF-IDF",
        descripcion="Comparación de rendimiento entre TF-IDF y BM25",
        configuracion={"top_k": 5, "chunk_size": 100}
    )
    
    # Agregar consulta
    query_id = db.add_query(
        experiment_id=experiment_id,
        query="¿Cuál es el monto máximo para viáticos nacionales?",
        categoria="viáticos",
        dificultad="fácil"
    )
    
    # Agregar resultados simulados
    mock_results = [
        {"id": "doc1", "text": "El monto máximo es S/ 150.00", "score": 0.9, "method": "tfidf"},
        {"id": "doc2", "text": "Para viáticos nacionales...", "score": 0.8, "method": "tfidf"}
    ]
    
    db.add_results(query_id, experiment_id, mock_results, execution_time=0.5)
    
    # Agregar métricas
    metrics = {
        "precision": 0.8,
        "recall": 0.7,
        "f1_score": 0.75,
        "response_time": 0.5
    }
    
    db.add_metrics(query_id, experiment_id, metrics)
    
    # Finalizar experimento
    db.finish_experiment(experiment_id)
    
    # Obtener resultados
    results = db.get_experiment_results(experiment_id)
    print(f"Experimento completado: {results['experimento']['nombre']}")
    print(f"Consultas procesadas: {results['resumen']['total_consultas']}")
    
    # Exportar a JSON
    db.export_experiment_to_json(experiment_id, "data/evaluation/test_experiment.json") 