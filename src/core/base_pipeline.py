#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Clase base abstracta para pipelines RAG.
Define la interfaz común para todos los pipelines de recuperación y generación.

Autor: Hanns
Fecha: 2025-06-05
"""

import os
import time
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime

from src.config.rag_config import RAGConfig

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('BasePipeline')


class BasePipeline(ABC):
    """
    Pipeline base abstracto para sistemas RAG.
    
    Define la interfaz común y funcionalidades compartidas para todos los pipelines
    de recuperación y generación de respuestas.
    """
    
    def __init__(self, config: Optional[RAGConfig] = None):
        """
        Inicializa el pipeline base.
        
        Args:
            config: Configuración del pipeline. Si es None, se usa la configuración por defecto.
        """
        self.config = config or RAGConfig()
        self.components = {}
        self.metrics = {
            "latency": {},
            "tokens": {},
            "memory": {},
        }
        logger.info(f"Inicializando {self.__class__.__name__} con configuración {self.config.version}")
    
    @abstractmethod
    def load_components(self) -> None:
        """
        Carga los componentes del pipeline según la configuración.
        
        Esta función debe ser implementada por cada subclase para cargar
        los componentes específicos del pipeline.
        """
        pass
    
    @abstractmethod
    def query(self, question: str, **kwargs) -> Dict[str, Any]:
        """
        Ejecuta una consulta en el pipeline.
        
        Args:
            question: Pregunta o consulta del usuario
            **kwargs: Argumentos adicionales específicos del pipeline
            
        Returns:
            Respuesta estructurada con resultados y metadatos
        """
        pass
    
    def track_time(self, component_name: str) -> callable:
        """
        Decorador para medir el tiempo de ejecución de un componente.
        
        Args:
            component_name: Nombre del componente a medir
            
        Returns:
            Función decoradora
        """
        def time_tracker(func):
            def wrapper(*args, **kwargs):
                if not self.config.metrics.track_latency:
                    return func(*args, **kwargs)
                
                start_time = time.time()
                result = func(*args, **kwargs)
                elapsed_time = time.time() - start_time
                
                if component_name not in self.metrics["latency"]:
                    self.metrics["latency"][component_name] = []
                
                self.metrics["latency"][component_name].append(elapsed_time)
                logger.debug(f"{component_name} completado en {elapsed_time:.4f} segundos")
                
                return result
            return wrapper
        return time_tracker
    
    def evaluate(self, dataset_path: str, metrics: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Evalúa el pipeline con un dataset.
        
        Args:
            dataset_path: Ruta al dataset de evaluación
            metrics: Lista de métricas a evaluar. Si es None, se usan todas las disponibles.
            
        Returns:
            Resultados de la evaluación
        """
        try:
            # Cargar dataset
            with open(dataset_path, 'r', encoding='utf-8') as f:
                dataset = json.load(f)
            
            results = []
            start_time = time.time()
            
            # Procesar cada pregunta
            for i, item in enumerate(dataset):
                logger.info(f"Evaluando pregunta {i+1}/{len(dataset)}: {item['question']}")
                
                # Ejecutar consulta
                response = self.query(item['question'])
                
                # Guardar resultado
                results.append({
                    "query_id": item.get("query_id", f"Q{i+1:03d}"),
                    "question": item["question"],
                    "category": item.get("category", "unknown"),
                    "ground_truth": item.get("ground_truth_answer", ""),
                    "response": response,
                    "metadata": {
                        "latency": response.get("metadata", {}).get("time_taken", 0),
                        "timestamp": datetime.now().isoformat(),
                    }
                })
            
            total_time = time.time() - start_time
            
            # Calcular métricas agregadas
            aggregated = {
                "total_questions": len(dataset),
                "total_time": total_time,
                "avg_time_per_question": total_time / len(dataset) if dataset else 0,
                "timestamp": datetime.now().isoformat(),
            }
            
            # Exportar resultados si está habilitado
            if self.config.metrics.export_metrics:
                os.makedirs(self.config.metrics.export_path, exist_ok=True)
                output_path = os.path.join(
                    self.config.metrics.export_path,
                    f"evaluation_{self.__class__.__name__}_{int(time.time())}.json"
                )
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump({"results": results, "aggregated": aggregated}, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Resultados de evaluación guardados en {output_path}")
            
            return {"results": results, "aggregated": aggregated}
            
        except Exception as e:
            logger.error(f"Error en evaluación: {str(e)}")
            return {"error": str(e)}
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Obtiene las métricas acumuladas del pipeline.
        
        Returns:
            Métricas del pipeline
        """
        # Calcular estadísticas para latencia
        latency_stats = {}
        for component, times in self.metrics["latency"].items():
            if times:
                latency_stats[component] = {
                    "min": min(times),
                    "max": max(times),
                    "avg": sum(times) / len(times),
                    "total": sum(times),
                    "calls": len(times),
                }
        
        return {
            "latency": latency_stats,
            "tokens": self.metrics["tokens"],
            "memory": self.metrics["memory"],
            "timestamp": datetime.now().isoformat(),
        }
    
    def reset_metrics(self) -> None:
        """
        Reinicia las métricas acumuladas.
        """
        self.metrics = {
            "latency": {},
            "tokens": {},
            "memory": {},
        }
        logger.info("Métricas reiniciadas")
    
    def __str__(self) -> str:
        """
        Representación en string del pipeline.
        """
        return f"{self.__class__.__name__}(version={self.config.version}, components={list(self.components.keys())})"
