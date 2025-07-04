import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors
from pathlib import Path

# Use the actual transformers vectorstore path
VECTORSTORE = "data/vectorstores/transformers.pkl"

def load_vectorstore():
    """Load transformers vectorstore and create index on demand"""
    vectorstore_path = Path(VECTORSTORE)
    if not vectorstore_path.exists():
        # Skip test if vectorstore doesn't exist
        import pytest
        pytest.skip(f"Vectorstore not found: {VECTORSTORE}")
    
    with open(VECTORSTORE, "rb") as f:
        data = pickle.load(f)
    
    # Extract embeddings and chunks
    embeddings = data["embeddings"]
    chunks = data["chunks"]
    
    # Create NearestNeighbors index
    index = NearestNeighbors(n_neighbors=5, metric='cosine')
    index.fit(embeddings)
    
    return index, chunks

def test_semantic_search_top1():
    index, chunks = load_vectorstore()
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    query = "tope diario de viáticos"
    q_emb = model.encode([query])
    distances, indices = index.kneighbors(q_emb)
    top_text = chunks[indices[0][0]]["texto"].lower()
    assert "viáticos" in top_text or "tope" in top_text or "diario" in top_text
