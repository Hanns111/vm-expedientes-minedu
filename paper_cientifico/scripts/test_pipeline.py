#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de prueba para el pipeline RAG de MINEDU.

Este script realiza una prueba de sanity check del pipeline RAG
utilizando una configuración simplificada y una sola consulta.

Autor: Hanns
Fecha: 2025-06-06
"""

import os
import sys
import json
import logging
from datetime import datetime

# Añadir el directorio raíz al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Importar el pipeline y la configuración
from src.pipelines.minedu_pipeline import MineduRAGPipeline
from src.config.rag_config import RAGConfig

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_pipeline')


def run_sanity_check(config_path, test_query=None):
    """
    Ejecuta una prueba de sanity check del pipeline RAG.
    
    Args:
        config_path: Ruta al archivo de configuración
        test_query: Consulta de prueba (opcional)
        
    Returns:
        Resultado de la consulta
    """
    logger.info(f"Iniciando prueba de sanity check con configuración: {config_path}")
    
    # Cargar configuración
    try:
        config = RAGConfig.from_yaml(config_path)
        logger.info(f"Configuración cargada correctamente: {config.general.name} v{config.general.version}")
    except Exception as e:
        logger.error(f"Error al cargar la configuración: {str(e)}")
        return None
    
    # Si no se proporciona una consulta, cargar una del dataset de evaluación
    if test_query is None:
        try:
            dataset_path = config.evaluation.dataset_path
            with open(dataset_path, 'r', encoding='utf-8') as f:
                dataset = json.load(f)
                # Tomar la primera pregunta del dataset
                test_query = dataset[0]["question"]
                logger.info(f"Consulta de prueba cargada del dataset: {test_query}")
        except Exception as e:
            logger.error(f"Error al cargar consulta del dataset: {str(e)}")
            test_query = "¿Cuál es el monto máximo para viáticos nacionales?"
            logger.info(f"Usando consulta de prueba por defecto: {test_query}")
    
    # Crear pipeline
    try:
        logger.info("Creando pipeline RAG...")
        pipeline = MineduRAGPipeline(config=config)
        logger.info("Pipeline creado correctamente")
    except Exception as e:
        logger.error(f"Error al crear el pipeline: {str(e)}")
        return None
    
    # Ejecutar consulta
    try:
        logger.info(f"Ejecutando consulta: {test_query}")
        start_time = datetime.now()
        result = pipeline.query(test_query)
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        logger.info(f"Consulta ejecutada en {execution_time:.2f} segundos")
        
        # Guardar resultado
        output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results", "sanity_check_result.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        logger.info(f"Resultado guardado en {output_path}")
        
        return result
    except Exception as e:
        logger.error(f"Error al ejecutar la consulta: {str(e)}")
        return None


def main():
    """
    Función principal.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Prueba de sanity check del pipeline RAG")
    parser.add_argument("--config", type=str, default="src/config/minedu_config_test.yaml",
                        help="Ruta al archivo de configuración")
    parser.add_argument("--query", type=str, default=None,
                        help="Consulta de prueba (opcional)")
    
    args = parser.parse_args()
    
    # Ejecutar prueba
    result = run_sanity_check(args.config, args.query)
    
    # Mostrar resultado
    if result:
        print("\n=== RESULTADO DE LA CONSULTA ===")
        if "results" in result and result["results"]:
            for i, res in enumerate(result["results"]):
                print(f"\nResultado {i+1}:")
                print(f"Contenido: {res.get('content', '')[:200]}...")  # Mostrar solo los primeros 200 caracteres
                print(f"Puntuación: {res.get('score', 0):.4f}")
                print(f"Fuente: {res.get('metadata', {}).get('source', 'Desconocida')}")
        
        if "metrics" in result:
            print("\nMétricas:")
            for metric, value in result["metrics"].items():
                print(f"- {metric}: {value}")
        
        print("\nSanity check completado con éxito.")
    else:
        print("\nError en el sanity check. Revisa los logs para más detalles.")


if __name__ == "__main__":
    main()
