import pickle
from sentence_transformers import SentenceTransformer
from src.core.config.security_config import SecurityConfig

VECTORSTORE = str(SecurityConfig.VECTORSTORE_PATH)

def load_vectorstore():
    with open(VECTORSTORE, "rb") as f:
        data = pickle.load(f)
    return data["index"], data["chunks"]

def test_semantic_search_top1():
    index, chunks = load_vectorstore()
    model = SentenceTransformer("all-MiniLM-L6-v2")
    query = "tope diario de viáticos"
    q_emb = model.encode([query])
    distances, indices = index.kneighbors(q_emb)
    top_text = chunks[indices[0][0]]["texto"].lower()
    assert "viáticos" in top_text or "tope diario" in top_text
