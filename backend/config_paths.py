from pathlib import Path

class ProjectPaths:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    DATA_DIR = PROJECT_ROOT / "data"
    VECTORSTORES_DIR = DATA_DIR / "vectorstores"
    BM25_VECTORSTORE = VECTORSTORES_DIR / "bm25.pkl"
    TFIDF_VECTORSTORE = VECTORSTORES_DIR / "tfidf.pkl"
    TRANSFORMERS_VECTORSTORE = VECTORSTORES_DIR / "transformers.pkl"
