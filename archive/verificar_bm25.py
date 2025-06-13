#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificación del estado actual de BM25
"""

import pickle
import json
import os

print("=== VERIFICACIÓN ACTUAL ===")

# 1. Verificar vectorstore BM25
print("1. Verificando vectorstore BM25:")
vectorstore_path = "data/processed/vectorstore_bm25_test.pkl"
if os.path.exists(vectorstore_path):
    try:
        with open(vectorstore_path, "rb") as f:
            vs = pickle.load(f)
        print("✅ Vectorstore carga OK")
        print(f"Tipo: {type(vs)}")
        if hasattr(vs, 'chunks'):
            print(f"Chunks en vectorstore: {len(vs.chunks)}")
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("❌ Vectorstore no existe")

# 2. Verificar chunks (estos SÍ funcionan)
print("\n2. Verificando chunks (estos SÍ funcionan):")
chunks_path = "data/processed/chunks.json"
if os.path.exists(chunks_path):
    try:
        with open(chunks_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        print(f"✅ Chunks: {len(chunks)} fragmentos")
        if chunks:
            print(f"Ejemplo de claves: {list(chunks[0].keys())}")
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("❌ Chunks no existen")

# 3. Verificar otros vectorstores que funcionan
print("\n3. Verificando otros vectorstores (para comparar):")
other_vectorstores = [
    "data/processed/vectorstore_semantic_full_v2.pkl",
    "data/processed/vectorstore_transformers_test.pkl"
]

for vs_path in other_vectorstores:
    if os.path.exists(vs_path):
        try:
            with open(vs_path, "rb") as f:
                vs = pickle.load(f)
            print(f"✅ {os.path.basename(vs_path)}: OK")
        except Exception as e:
            print(f"❌ {os.path.basename(vs_path)}: {e}")
    else:
        print(f"⚠️ {os.path.basename(vs_path)}: No existe") 