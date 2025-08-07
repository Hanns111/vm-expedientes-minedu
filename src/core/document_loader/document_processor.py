"""
Procesador de documentos básico
"""
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

class ChunkingStrategy(Enum):
    """Estrategias de chunking"""
    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"

@dataclass
class ProcessingConfig:
    """Configuración de procesamiento"""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE
    enable_ocr: bool = False
    language: str = "es"

class DocumentProcessor:
    """Procesador básico de documentos"""

    def __init__(self, config: Optional[ProcessingConfig] = None):
        self.config = config or ProcessingConfig()

    def process(self, content: str) -> str:
        """Procesar contenido"""
        # Limpieza básica
        processed = content.strip()
        # Normalizar espacios
        processed = " ".join(processed.split())
        return processed

    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """Dividir texto en chunks"""
        chunks = []
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap
        
        for i in range(0, len(text), chunk_size - overlap):
            chunk_text = text[i:i + chunk_size]
            if chunk_text.strip():
                chunks.append({
                    "text": chunk_text,
                    "start_index": i,
                    "end_index": min(i + chunk_size, len(text)),
                    "chunk_id": len(chunks)
                })
        
        return chunks

    def extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extraer metadatos del contenido"""
        return {
            "length": len(content),
            "word_count": len(content.split()),
            "language": self.config.language,
            "strategy": self.config.strategy.value
        } 