"""Centralised project path configuration."""

from pathlib import Path

class ProjectPaths:
    """Centralised paths used across the project."""

    PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

    # Directories
    DATA_DIR: Path = PROJECT_ROOT / "data"
    PROCESSED_DIR: Path = DATA_DIR / "processed"
    VECTORSTORES_DIR: Path = DATA_DIR / "vectorstores"
    RESULTS_DIR: Path = DATA_DIR / "results"

    # Files
    CHUNKS_FILE: Path = PROCESSED_DIR / "chunks.json"

    # Vectorstores
    BM25_VECTORSTORE: Path = VECTORSTORES_DIR / "bm25.pkl"
    TFIDF_VECTORSTORE: Path = VECTORSTORES_DIR / "tfidf.pkl"
    TRANSFORMERS_VECTORSTORE: Path = VECTORSTORES_DIR / "transformers.pkl"

    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure main directories exist."""
        for attr in dir(cls):
            if attr.endswith("_DIR"):
                value = getattr(cls, attr)
                if isinstance(value, Path):
                    value.mkdir(parents=True, exist_ok=True)

    @classmethod
    def rel(cls, path: Path) -> str:
        try:
            return str(path.relative_to(cls.PROJECT_ROOT))
        except ValueError:
            return str(path)

# Create directories immediately
ProjectPaths.ensure_directories() 