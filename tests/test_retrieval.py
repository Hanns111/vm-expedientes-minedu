#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Basic tests for the search system.
"""

import pytest
from src.core.retrieval import BM25Retriever, TFIDFRetriever, TransformerRetriever


def test_bm25_retriever():
    """Test BM25 retriever functionality."""
    # This test requires a valid vectorstore
    # For now, just test that the class can be imported
    assert BM25Retriever is not None


def test_tfidf_retriever():
    """Test TF-IDF retriever functionality."""
    # This test requires a valid vectorstore
    # For now, just test that the class can be imported
    assert TFIDFRetriever is not None


def test_transformer_retriever():
    """Test Transformer retriever functionality."""
    # This test requires a valid vectorstore
    # For now, just test that the class can be imported
    assert TransformerRetriever is not None


if __name__ == "__main__":
    pytest.main([__file__])
