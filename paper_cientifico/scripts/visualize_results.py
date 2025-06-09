#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para visualizar resultados de evaluación del pipeline RAG de MINEDU.

Este script genera gráficos y visualizaciones a partir de los resultados de evaluación
y estudios de ablación para facilitar el análisis y la presentación de resultados.

Autor: Hanns
Fecha: 2025-06-05
"""

import os
import json
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime

# Configuración de estilo para gráficos
plt.style.use('ggplot')
sns.set(style="whitegrid")
sns.set_palette("colorblind")

# Configuración de tamaño de fuente
plt.rcParams.update({'font.size': 12})


def load_results(results_path: str) -> Dict[str, Any]:
    """
    Carga resultados de evaluación desde un archivo JSON.
    
    Args:
        results_path: Ruta al archivo de resultados
        
    Returns:
        Resultados cargados
    """
    with open(results_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_metrics_summary(results: Dict[str, Any]) -> pd.DataFrame:
    """
    Crea un resumen de métricas a partir de los resultados.
    
    Args:
        results: Resultados de evaluación
        
    Returns:
        DataFrame con resumen de métricas
    """
    if "results" not in results:
        print("Formato de resultados no válido")
        return pd.DataFrame()
    
    # Extraer métricas de cada resultado
    data = []
    for item in results["results"]:
        row = {
            "query_id": item.get("query_id", ""),
            "question": item.get("question", ""),
            "query_time": item.get("query_time", 0.0),
        }
        
        # Añadir métricas
        if "metrics" in item:
            for metric, value in item["metrics"].items():
                row[metric] = value
        
        data.append(row)
    
    return pd.DataFrame(data)


def plot_metrics_distribution(df: pd.DataFrame, output_dir: str):
    """
    Genera gráficos de distribución para cada métrica.
    
    Args:
        df: DataFrame con métricas
        output_dir: Directorio para guardar los gráficos
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Identificar columnas de métricas (excluyendo query_id, question, etc.)
    metric_cols = [col for col in df.columns if col not in ["query_id", "question"]]
    
    # Crear gráfico para cada métrica
    for metric in metric_cols:
        plt.figure(figsize=(10, 6))
        
        # Histograma con KDE
        sns.histplot(df[metric], kde=True)
        
        plt.title(f"Distribución de {metric}")
        plt.xlabel(metric)
        plt.ylabel("Frecuencia")
        plt.tight_layout()
        
        # Guardar gráfico
        plt.savefig(os.path.join(output_dir, f"dist_{metric}.png"), dpi=300)
        plt.close()


def plot_metrics_comparison(df: pd.DataFrame, output_dir: str):
    """
    Genera gráficos de comparación entre métricas.
    
    Args:
        df: DataFrame con métricas
        output_dir: Directorio para guardar los gráficos
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Identificar columnas de métricas (excluyendo query_id, question, etc.)
    metric_cols = [col for col in df.columns if col not in ["query_id", "question"]]
    
    # Crear matriz de correlación
    if len(metric_cols) > 1:
        plt.figure(figsize=(12, 10))
        corr = df[metric_cols].corr()
        mask = np.triu(np.ones_like(corr, dtype=bool))
        sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="coolwarm", square=True)
        
        plt.title("Correlación entre métricas")
        plt.tight_layout()
        
        # Guardar gráfico
        plt.savefig(os.path.join(output_dir, "metrics_correlation.png"), dpi=300)
        plt.close()
    
    # Crear gráfico de dispersión para pares de métricas relevantes
    if "token_overlap" in metric_cols and "exact_match" in metric_cols:
        plt.figure(figsize=(10, 6))
        sns.scatterplot(x="token_overlap", y="exact_match", data=df)
        
        plt.title("Relación entre solapamiento de tokens y coincidencia exacta")
        plt.xlabel("Solapamiento de tokens")
        plt.ylabel("Coincidencia exacta")
        plt.tight_layout()
        
        # Guardar gráfico
        plt.savefig(os.path.join(output_dir, "token_overlap_vs_exact_match.png"), dpi=300)
        plt.close()


def plot_query_time_analysis(df: pd.DataFrame, output_dir: str):
    """
    Genera gráficos de análisis de tiempo de consulta.
    
    Args:
        df: DataFrame con métricas
        output_dir: Directorio para guardar los gráficos
    """
    os.makedirs(output_dir, exist_ok=True)
    
    if "query_time" in df.columns:
        # Histograma de tiempos de consulta
        plt.figure(figsize=(10, 6))
        sns.histplot(df["query_time"], kde=True)
        
        plt.title("Distribución de tiempos de consulta")
        plt.xlabel("Tiempo (segundos)")
        plt.ylabel("Frecuencia")
        plt.tight_layout()
        
        # Guardar gráfico
        plt.savefig(os.path.join(output_dir, "query_time_distribution.png"), dpi=300)
        plt.close()
        
        # Gráfico de barras de tiempos por consulta
        plt.figure(figsize=(14, 8))
        
        # Ordenar por tiempo de consulta
        sorted_df = df.sort_values("query_time", ascending=False)
        sns.barplot(x="query_id", y="query_time", data=sorted_df)
        
        plt.title("Tiempo de consulta por pregunta")
        plt.xlabel("ID de pregunta")
        plt.ylabel("Tiempo (segundos)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Guardar gráfico
        plt.savefig(os.path.join(output_dir, "query_time_by_question.png"), dpi=300)
        plt.close()


def plot_ablation_results(results: Dict[str, Any], output_dir: str):
    """
    Genera gráficos para resultados de estudios de ablación.
    
    Args:
        results: Resultados del estudio de ablación
        output_dir: Directorio para guardar los gráficos
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Verificar si es un estudio de ablación
    if "ablation_results" not in results:
        print("No se encontraron resultados de ablación")
        return
    
    ablation_results = results["ablation_results"]
    
    # Convertir a DataFrame
    data = []
    for config_name, config_results in ablation_results.items():
        row = {"config": config_name}
        row.update(config_results.get("aggregated", {}))
        data.append(row)
    
    df = pd.DataFrame(data)
    
    # Identificar métricas disponibles
    metric_cols = [col for col in df.columns if col.startswith("avg_") and col != "avg_query_time"]
    
    # Crear gráfico de barras para cada métrica
    for metric in metric_cols:
        plt.figure(figsize=(12, 8))
        
        # Ordenar por valor de métrica
        sorted_df = df.sort_values(metric, ascending=False)
        sns.barplot(x="config", y=metric, data=sorted_df)
        
        plt.title(f"Comparación de {metric} por configuración")
        plt.xlabel("Configuración")
        plt.ylabel(metric)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Guardar gráfico
        plt.savefig(os.path.join(output_dir, f"ablation_{metric}.png"), dpi=300)
        plt.close()
    
    # Gráfico de tiempo de consulta
    if "avg_query_time" in df.columns:
        plt.figure(figsize=(12, 8))
        
        # Ordenar por tiempo de consulta
        sorted_df = df.sort_values("avg_query_time", ascending=True)
        sns.barplot(x="config", y="avg_query_time", data=sorted_df)
        
        plt.title("Tiempo promedio de consulta por configuración")
        plt.xlabel("Configuración")
        plt.ylabel("Tiempo promedio (segundos)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Guardar gráfico
        plt.savefig(os.path.join(output_dir, "ablation_query_time.png"), dpi=300)
        plt.close()


def generate_summary_report(results: Dict[str, Any], df: pd.DataFrame, output_path: str):
    """
    Genera un informe de resumen en formato Markdown.
    
    Args:
        results: Resultados de evaluación
        df: DataFrame con métricas
        output_path: Ruta para guardar el informe
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        # Título y fecha
        f.write(f"# Informe de Evaluación del Pipeline RAG MINEDU\n\n")
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Resumen general
        f.write("## Resumen General\n\n")
        
        if "aggregated" in results:
            f.write("| Métrica | Valor |\n")
            f.write("|---------|-------|\n")
            
            for metric, value in results["aggregated"].items():
                if isinstance(value, (int, float)):
                    f.write(f"| {metric} | {value:.4f} |\n")
                else:
                    f.write(f"| {metric} | {value} |\n")
        
        # Estadísticas descriptivas
        f.write("\n## Estadísticas Descriptivas\n\n")
        
        metric_cols = [col for col in df.columns if col not in ["query_id", "question"]]
        if metric_cols:
            stats = df[metric_cols].describe()
            f.write(stats.to_markdown())
        
        # Mejores y peores preguntas
        f.write("\n## Análisis por Pregunta\n\n")
        
        if "token_overlap" in df.columns:
            f.write("### Mejores Preguntas (por solapamiento de tokens)\n\n")
            best = df.sort_values("token_overlap", ascending=False).head(3)
            f.write(best[["query_id", "question", "token_overlap"]].to_markdown(index=False))
            
            f.write("\n### Peores Preguntas (por solapamiento de tokens)\n\n")
            worst = df.sort_values("token_overlap", ascending=True).head(3)
            f.write(worst[["query_id", "question", "token_overlap"]].to_markdown(index=False))
        
        # Conclusiones
        f.write("\n## Conclusiones\n\n")
        f.write("- Este informe presenta un análisis automático de los resultados de evaluación.\n")
        f.write("- Se recomienda revisar los gráficos generados para un análisis visual más detallado.\n")
        f.write("- Las métricas principales a considerar son: token_overlap, faithfulness (si está disponible) y tiempo de consulta.\n")


def main():
    """
    Función principal.
    """
    parser = argparse.ArgumentParser(description="Visualizar resultados de evaluación del pipeline RAG")
    parser.add_argument("--results", type=str, required=True,
                        help="Ruta al archivo de resultados JSON")
    parser.add_argument("--output-dir", type=str, default="paper_cientifico/visualizations",
                        help="Directorio para guardar las visualizaciones")
    
    args = parser.parse_args()
    
    # Cargar resultados
    results = load_results(args.results)
    
    # Crear directorio de salida
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Crear DataFrame con métricas
    if "results" in results:
        df = create_metrics_summary(results)
        
        # Generar visualizaciones
        plot_metrics_distribution(df, os.path.join(args.output_dir, "distributions"))
        plot_metrics_comparison(df, os.path.join(args.output_dir, "comparisons"))
        plot_query_time_analysis(df, os.path.join(args.output_dir, "query_time"))
        
        # Generar informe de resumen
        generate_summary_report(results, df, os.path.join(args.output_dir, "summary_report.md"))
        
        print(f"Visualizaciones generadas en {args.output_dir}")
    
    # Visualizar resultados de ablación
    if "ablation_results" in results:
        plot_ablation_results(results, os.path.join(args.output_dir, "ablation"))
        print(f"Visualizaciones de ablación generadas en {os.path.join(args.output_dir, 'ablation')}")


if __name__ == "__main__":
    main()
