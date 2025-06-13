#!/usr/bin/env python3
"""
SPRINT 1.2 - PARTE 1: Setup de Evaluadores Científicos
Implementa sistema de evaluación rigurosa BM25 vs TF-IDF para paper científico

OBJETIVO: Crear infraestructura de evaluación para generar métricas científicas
RESULTADO: Evaluadores configurados listos para experimentos rigurosos
"""

import json
import os
import sys
from pathlib import Path
import numpy as np
from collections import defaultdict, Counter
import time

# Verificar dependencias necesarias
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    print("[OK] scikit-learn disponible")
except ImportError:
    print("[ERROR] scikit-learn no encontrado. Instalar con: pip install scikit-learn")
    sys.exit(1)

try:
    from rank_bm25 import BM25Okapi
    print("[OK] rank-bm25 disponible")
except ImportError:
    print("[ERROR] rank-bm25 no encontrado. Instalar con: pip install rank-bm25")
    sys.exit(1)

# Configuración
DATASET_PATH = "paper_cientifico/dataset/golden_dataset.json"
CHUNKS_PATH = "data/processed/chunks.json"
RESULTS_DIR = "paper_cientifico/results/sprint12"
REPORTS_DIR = "paper_cientifico/reports/sprint12"

class DocumentCorpus:
    """Gestor del corpus de documentos para evaluación"""
    
    def __init__(self, chunks_path):
        print("[INFO] Cargando corpus de documentos...")
        self.chunks_path = chunks_path
        self.chunks = self._load_chunks()
        self.corpus = self._prepare_corpus()
        print(f"[OK] Corpus cargado: {len(self.corpus)} documentos")
    
    def _load_chunks(self):
        """Cargar chunks de documentos"""
        if not os.path.exists(self.chunks_path):
            print(f"[ERROR] Chunks no encontrados: {self.chunks_path}")
            return []
        
        try:
            with open(self.chunks_path, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
            print(f"[OK] Chunks cargados: {len(chunks)} fragmentos")
            return chunks
        except Exception as e:
            print(f"[ERROR] Error cargando chunks: {e}")
            return []
    
    def _prepare_corpus(self):
        """Preparar corpus para búsqueda"""
        if not self.chunks:
            return []
        
        # Extraer texto de chunks
        corpus = []
        for chunk in self.chunks:
            if isinstance(chunk, dict):
                text = chunk.get('texto', '') or chunk.get('text', '')
            else:
                text = str(chunk)
            
            # Limpiar y preparar texto
            text = text.strip()
            if text:
                corpus.append(text)
        
        return corpus
    
    def get_document_by_index(self, index):
        """Obtener documento por índice"""
        if 0 <= index < len(self.corpus):
            return self.corpus[index]
        return None

class TFIDFRetriever:
    """Evaluador TF-IDF para comparación científica"""
    
    def __init__(self, corpus):
        print("[INFO] Configurando evaluador TF-IDF...")
        self.corpus = corpus
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words=None,  # Mantener todas las palabras para docs normativos
            max_features=10000,
            ngram_range=(1, 2),  # Unigrams y bigrams
            min_df=1,
            max_df=0.95
        )
        self.document_vectors = None
        self._fit_corpus()
    
    def _fit_corpus(self):
        """Entrenar vectorizador con corpus"""
        try:
            self.document_vectors = self.vectorizer.fit_transform(self.corpus)
            print(f"[OK] TF-IDF entrenado: {self.document_vectors.shape[0]} docs, {self.document_vectors.shape[1]} features")
        except Exception as e:
            print(f"[ERROR] Error entrenando TF-IDF: {e}")
            self.document_vectors = None
    
    def search(self, query, top_k=10):
        """Buscar documentos relevantes usando TF-IDF"""
        if self.document_vectors is None:
            return []
        
        try:
            # Vectorizar query
            query_vector = self.vectorizer.transform([query])
            
            # Calcular similitudes
            similarities = cosine_similarity(query_vector, self.document_vectors).flatten()
            
            # Obtener top-k documentos
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0:  # Solo documentos con similitud > 0
                    results.append({
                        'doc_index': int(idx),
                        'score': float(similarities[idx]),
                        'content': self.corpus[idx][:200] + "..." if len(self.corpus[idx]) > 200 else self.corpus[idx]
                    })
            
            return results
            
        except Exception as e:
            print(f"[ERROR] Error en búsqueda TF-IDF: {e}")
            return []

class BM25Retriever:
    """Evaluador BM25 para comparación científica"""
    
    def __init__(self, corpus, k1=1.5, b=0.75):
        print("[INFO] Configurando evaluador BM25...")
        self.corpus = corpus
        self.k1 = k1
        self.b = b
        self.tokenized_corpus = self._tokenize_corpus()
        self.bm25 = self._fit_corpus()
    
    def _tokenize_corpus(self):
        """Tokenizar corpus para BM25"""
        tokenized = []
        for doc in self.corpus:
            # Tokenización simple por espacios (para docs normativos)
            tokens = doc.lower().split()
            tokenized.append(tokens)
        return tokenized
    
    def _fit_corpus(self):
        """Entrenar BM25 con corpus"""
        try:
            bm25 = BM25Okapi(self.tokenized_corpus, k1=self.k1, b=self.b)
            print(f"[OK] BM25 entrenado: {len(self.tokenized_corpus)} docs, k1={self.k1}, b={self.b}")
            return bm25
        except Exception as e:
            print(f"[ERROR] Error entrenando BM25: {e}")
            return None
    
    def search(self, query, top_k=10):
        """Buscar documentos relevantes usando BM25"""
        if self.bm25 is None:
            return []
        
        try:
            # Tokenizar query
            query_tokens = query.lower().split()
            
            # Obtener scores BM25
            scores = self.bm25.get_scores(query_tokens)
            
            # Obtener top-k documentos
            top_indices = np.argsort(scores)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                if scores[idx] > 0:  # Solo documentos con score > 0
                    results.append({
                        'doc_index': int(idx),
                        'score': float(scores[idx]),
                        'content': self.corpus[idx][:200] + "..." if len(self.corpus[idx]) > 200 else self.corpus[idx]
                    })
            
            return results
            
        except Exception as e:
            print(f"[ERROR] Error en búsqueda BM25: {e}")
            return []

class EvaluationMetrics:
    """Calculador de métricas científicas para evaluación"""
    
    @staticmethod
    def precision_at_k(retrieved_docs, relevant_docs, k):
        """Calcular Precision@K"""
        if k == 0:
            return 0.0
        
        retrieved_k = retrieved_docs[:k]
        relevant_retrieved = len([doc for doc in retrieved_k if doc in relevant_docs])
        return relevant_retrieved / k
    
    @staticmethod
    def recall_at_k(retrieved_docs, relevant_docs, k):
        """Calcular Recall@K"""
        if not relevant_docs:
            return 0.0
        
        retrieved_k = retrieved_docs[:k]
        relevant_retrieved = len([doc for doc in retrieved_k if doc in relevant_docs])
        return relevant_retrieved / len(relevant_docs)
    
    @staticmethod
    def f1_at_k(retrieved_docs, relevant_docs, k):
        """Calcular F1@K"""
        precision = EvaluationMetrics.precision_at_k(retrieved_docs, relevant_docs, k)
        recall = EvaluationMetrics.recall_at_k(retrieved_docs, relevant_docs, k)
        
        if precision + recall == 0:
            return 0.0
        
        return 2 * (precision * recall) / (precision + recall)
    
    @staticmethod
    def mean_reciprocal_rank(retrieved_docs_list, relevant_docs_list):
        """Calcular Mean Reciprocal Rank (MRR)"""
        reciprocal_ranks = []
        
        for retrieved_docs, relevant_docs in zip(retrieved_docs_list, relevant_docs_list):
            rank = 0
            for i, doc in enumerate(retrieved_docs, 1):
                if doc in relevant_docs:
                    rank = 1.0 / i
                    break
            reciprocal_ranks.append(rank)
        
        return np.mean(reciprocal_ranks) if reciprocal_ranks else 0.0
    
    @staticmethod
    def dcg_at_k(retrieved_docs, relevant_docs, k):
        """Calcular Discounted Cumulative Gain@K"""
        dcg = 0.0
        for i, doc in enumerate(retrieved_docs[:k]):
            if doc in relevant_docs:
                dcg += 1.0 / np.log2(i + 2)  # +2 porque log2(1) = 0
        return dcg
    
    @staticmethod
    def ndcg_at_k(retrieved_docs, relevant_docs, k):
        """Calcular Normalized Discounted Cumulative Gain@K"""
        dcg = EvaluationMetrics.dcg_at_k(retrieved_docs, relevant_docs, k)
        
        # IDCG: DCG ideal (todos los docs relevantes en orden perfecto)
        ideal_order = relevant_docs[:k]
        idcg = EvaluationMetrics.dcg_at_k(ideal_order, relevant_docs, k)
        
        return dcg / idcg if idcg > 0 else 0.0

def setup_evaluation_environment():
    """Configurar entorno de evaluación"""
    print("[INFO] Configurando entorno de evaluación...")
    
    # Crear directorios necesarios
    directories = [RESULTS_DIR, REPORTS_DIR]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"[OK] Directorio listo: {directory}")
    
    # Verificar dataset expandido
    if not os.path.exists(DATASET_PATH):
        print(f"[ERROR] Dataset expandido no encontrado: {DATASET_PATH}")
        return False
    
    # Verificar chunks de documentos
    if not os.path.exists(CHUNKS_PATH):
        print(f"[ERROR] Chunks de documentos no encontrados: {CHUNKS_PATH}")
        return False
    
    print("[OK] Entorno de evaluación configurado correctamente")
    return True

def load_evaluation_dataset():
    """Cargar dataset expandido para evaluación"""
    print("[INFO] Cargando dataset de evaluación...")
    
    try:
        with open(DATASET_PATH, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        print(f"[OK] Dataset cargado: {len(dataset)} preguntas")
        
        # Manejar tanto query_type directo como dentro de metadata
        def get_query_type(q):
            if 'query_type' in q:
                return q['query_type']
            elif 'metadata' in q and 'query_type' in q['metadata']:
                return q['metadata']['query_type']
            return "unknown"
        
        # Mostrar distribución para confirmación
        query_types = Counter(get_query_type(q) for q in dataset)
        print(f"[INFO] Distribución: {dict(query_types)}")
        
        return dataset
        
    except Exception as e:
        print(f"[ERROR] Error cargando dataset: {e}")
        return None

def main_part1():
    """Ejecutar Parte 1: Setup de evaluadores"""
    print("[INFO] SPRINT 1.2 - PARTE 1: SETUP DE EVALUADORES CIENTÍFICOS")
    print("[INFO] Preparando infraestructura para evaluación BM25 vs TF-IDF")
    print("=" * 65)
    
    # Paso 1: Configurar entorno
    if not setup_evaluation_environment():
        print("[ERROR] Error en configuración del entorno")
        return False
    
    # Paso 2: Cargar dataset
    dataset = load_evaluation_dataset()
    if not dataset:
        print("[ERROR] Error cargando dataset de evaluación")
        return False
    
    # Paso 3: Cargar corpus
    corpus = DocumentCorpus(CHUNKS_PATH)
    if not corpus.corpus:
        print("[ERROR] Error cargando corpus de documentos")
        return False
    
    # Paso 4: Configurar evaluadores
    print("\n[INFO] Configurando evaluadores...")
    
    # TF-IDF Retriever
    tfidf_retriever = TFIDFRetriever(corpus.corpus)
    if tfidf_retriever.document_vectors is None:
        print("[ERROR] Error configurando TF-IDF")
        return False
    
    # BM25 Retriever
    bm25_retriever = BM25Retriever(corpus.corpus)
    if bm25_retriever.bm25 is None:
        print("[ERROR] Error configurando BM25")
        return False
    
    # Paso 5: Prueba de funcionamiento
    print("\n[INFO] Ejecutando pruebas de funcionamiento...")
    
    test_query = "¿Cuál es el monto máximo para viáticos?"
    
    # Probar TF-IDF
    tfidf_results = tfidf_retriever.search(test_query, top_k=3)
    print(f"[OK] TF-IDF: {len(tfidf_results)} resultados")
    
    # Probar BM25
    bm25_results = bm25_retriever.search(test_query, top_k=3)
    print(f"[OK] BM25: {len(bm25_results)} resultados")
    
    # Probar métricas
    metrics = EvaluationMetrics()
    test_precision = metrics.precision_at_k([1, 2, 3], [1, 4, 5], 3)
    print(f"[OK] Métricas: Precision@3 = {test_precision:.3f}")
    
    print(f"\n[OK] PARTE 1 COMPLETADA EXITOSAMENTE")
    print(f"[INFO] Evaluadores configurados y funcionales")
    print(f"[INFO] Dataset: {len(dataset)} preguntas listas para evaluación")
    print(f"[INFO] Corpus: {len(corpus.corpus)} documentos indexados")
    print(f"[INFO] Listo para Parte 2: Ejecución de experimentos")
    
    return True

if __name__ == "__main__":
    success = main_part1()
    
    if success:
        print(f"\n[OK] ¡Parte 1 exitosa! Continuar con sprint12_part2_run_experiments.py")
    else:
        print(f"\n[ERROR] Parte 1 falló. Revisar errores y dependencias.")
        sys.exit(1)
