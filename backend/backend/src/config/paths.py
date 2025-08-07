"""Paths configuration for backend."""

from pathlib import Path

class ProjectPaths:
    """Project paths configuration."""
    
    PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]
    
    # Directories
    DATA_DIR: Path = PROJECT_ROOT / "data"
    VECTORSTORES_DIR: Path = DATA_DIR / "vectorstores"
    
    # Vectorstores
    BM25_VECTORSTORE: Path = VECTORSTORES_DIR / "bm25.pkl"
    TFIDF_VECTORSTORE: Path = VECTORSTORES_DIR / "tfidf.pkl"
    TRANSFORMERS_VECTORSTORE: Path = VECTORSTORES_DIR / "transformers.pkl"
    
    @classmethod
    def rel(cls, path: Path) -> str:
        """Get relative path from project root."""
        try:
            return str(path.relative_to(cls.PROJECT_ROOT))
        except ValueError:
            return str(path)
