"""
Configuración para integración LangChain/LangGraph
Migración de sistema hardcoded a RAG real
"""
import os
import json
from dataclasses import dataclass
from typing import Optional

@dataclass
class LangChainConfig:
    """Configuración para LangChain integration"""
    
    # OpenAI Configuration (cuando esté disponible)
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = "gpt-4o-mini"  # Modelo costo-efectivo
    embedding_model: str = "text-embedding-3-small"
    
    # Local Vector Store Configuration
    chroma_persist_directory: str = "./data/vectorstores/chromadb"
    chroma_collection_name: str = "minedu_documents"
    
    # Chunking Configuration  
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Retrieval Configuration
    retrieval_k: int = 5
    
    # Sistema Configuration
    temperature: float = 0.1  # Baja temperatura para precisión
    max_tokens: int = 1000
    
    # Fallback mode (sin APIs externas)
    use_openai: bool = False  # Cambiar a True cuando tengas API key
    fallback_mode: bool = True
    
    def validate(self) -> bool:
        """Validar configuración"""
        if self.use_openai and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY es requerido cuando use_openai=True")
        return True
    
    def to_dict(self) -> dict:
        """Convertir a diccionario para logging"""
        return {
            "openai_model": self.openai_model,
            "embedding_model": self.embedding_model,
            "chunk_size": self.chunk_size,
            "retrieval_k": self.retrieval_k,
            "use_openai": self.use_openai,
            "fallback_mode": self.fallback_mode
        }

# Instancia global
config = LangChainConfig()

def load_config_from_file(config_path: str) -> LangChainConfig:
    """Cargar configuración desde archivo JSON"""
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            return LangChainConfig(**config_data)
    return config

def save_config_to_file(config_obj: LangChainConfig, config_path: str):
    """Guardar configuración a archivo JSON"""
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_obj.to_dict(), f, indent=2, ensure_ascii=False)