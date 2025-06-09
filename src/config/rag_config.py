#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configuración para el sistema RAG utilizando Pydantic.
Define la estructura de configuración para todos los componentes del pipeline.

Autor: Hanns
Fecha: 2025-06-05
"""

from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field


class BM25Config(BaseModel):
    """Configuración para el retriever BM25."""
    
    enabled: bool = True
    vectorstore_path: str = "data/vectorstores/bm25_index.pkl"
    top_k: int = 10
    tokenizer_kwargs: Dict[str, Any] = Field(default_factory=dict)
    score_threshold: Optional[float] = None


class DenseRetrievalConfig(BaseModel):
    """Configuración para el retriever denso."""
    
    enabled: bool = True
    model_name: str = "intfloat/multilingual-e5-large"
    collection_name: str = "minedu_documents"
    persist_directory: str = "data/vectorstores/chroma"
    top_k: int = 10
    batch_size: int = 8
    max_length: int = 512
    normalize_embeddings: bool = True
    device: Optional[str] = None  # "cpu", "cuda", "cuda:0", etc.
    cache_dir: Optional[str] = None


class HybridFusionConfig(BaseModel):
    """Configuración para la fusión híbrida."""
    
    enabled: bool = True
    weights: Dict[str, float] = Field(default_factory=lambda: {"bm25": 0.4, "dense": 0.6})
    rrf_k: int = 60
    deduplicate: bool = True
    top_k: int = 10
    similarity_threshold: float = 0.95


class RerankerConfig(BaseModel):
    """Configuración para el reranker neural."""
    
    enabled: bool = True
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-12-v2"
    top_k: int = 5
    score_threshold: float = 0.1
    batch_size: int = 16
    max_length: int = 512
    device: Optional[str] = None


class ChunkingConfig(BaseModel):
    """Configuración para el chunking de documentos."""
    
    strategy: str = "fixed_size"  # "fixed_size", "semantic", "structural"
    chunk_size: int = 1024
    chunk_overlap: int = 200
    separators: List[str] = Field(default_factory=lambda: ["\n\n", "\n", ". ", " "])
    keep_separator: bool = False


class MetricsConfig(BaseModel):
    """Configuración para métricas y evaluación."""
    
    enabled: bool = True
    log_level: str = "INFO"
    track_latency: bool = True
    track_tokens: bool = False
    track_memory: bool = False
    export_metrics: bool = True
    export_path: str = "paper_cientifico/results/"


class RAGConfig(BaseModel):
    """Configuración completa para el pipeline RAG."""
    
    bm25: BM25Config = Field(default_factory=BM25Config)
    dense_retrieval: DenseRetrievalConfig = Field(default_factory=DenseRetrievalConfig)
    hybrid_fusion: HybridFusionConfig = Field(default_factory=HybridFusionConfig)
    reranking: RerankerConfig = Field(default_factory=RerankerConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    
    # Configuración general
    domain: str = "minedu"
    language: str = "es"
    country: str = "peru"
    version: str = "0.3.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la configuración a un diccionario."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "RAGConfig":
        """Crea una configuración desde un diccionario."""
        return cls(**config_dict)
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "RAGConfig":
        """Carga una configuración desde un archivo YAML."""
        import yaml
        with open(yaml_path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)
        return cls.from_dict(config_dict)
    
    def save_yaml(self, yaml_path: str) -> None:
        """Guarda la configuración en un archivo YAML."""
        import yaml
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)


if __name__ == "__main__":
    # Ejemplo de uso
    config = RAGConfig()
    print(config.model_dump_json(indent=2))
    
    # Modificar configuración
    config.bm25.top_k = 20
    config.dense_retrieval.model_name = "intfloat/multilingual-e5-large-instruct"
    
    # Guardar y cargar
    config.save_yaml("config_example.yaml")
    loaded_config = RAGConfig.from_yaml("config_example.yaml")
    print(loaded_config.bm25.top_k)  # Debería imprimir 20