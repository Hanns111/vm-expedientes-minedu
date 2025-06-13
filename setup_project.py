#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de configuración inicial del proyecto MINEDU Document Search System.

Este script configura el entorno del proyecto, crea la estructura de directorios
necesaria y prepara los datos de ejemplo.

Uso: python setup_project.py
"""

import os
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any


def setup_directories() -> None:
    """Crear estructura de directorios necesaria."""
    dirs = [
        "data/raw",
        "data/processed", 
        "data/vectorstores",
        "logs",
        "models/cache",
        "reports",
        "tests",
        "archive"
    ]
    
    print("📁 Creando estructura de directorios...")
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Creado: {dir_path}")


def download_sample_data() -> None:
    """Descargar o crear datos de ejemplo."""
    print("📄 Creando datos de ejemplo...")
    
    # Datos de ejemplo basados en la Directiva N° 011-2020-MINEDU
    sample_chunks = [
        {
            "id": 1,
            "texto": "El monto máximo diario para viáticos nacionales es de S/ 320.00 según la escala vigente.",
            "titulo": "Escala de Viáticos Nacionales",
            "metadatos": {"page": 1, "type": "normativa", "section": "viáticos"}
        },
        {
            "id": 2,
            "texto": "Los viáticos deben ser solicitados con diez (10) días hábiles de anticipación a la fecha programada para el viaje.",
            "titulo": "Plazo de Solicitud de Viáticos",
            "metadatos": {"page": 2, "type": "normativa", "section": "solicitud"}
        },
        {
            "id": 3,
            "texto": "El comisionado debe presentar una Declaración Jurada de Gastos para sustentar los gastos realizados.",
            "titulo": "Declaración Jurada de Gastos",
            "metadatos": {"page": 3, "type": "normativa", "section": "rendición"}
        },
        {
            "id": 4,
            "texto": "La autorización de viáticos corresponde al Jefe del órgano o unidad orgánica correspondiente.",
            "titulo": "Autorización de Viáticos",
            "metadatos": {"page": 4, "type": "normativa", "section": "autorización"}
        },
        {
            "id": 5,
            "texto": "Los gastos de viáticos se rinden dentro de los cinco (5) días hábiles posteriores al término de la comisión.",
            "titulo": "Plazo de Rendición",
            "metadatos": {"page": 5, "type": "normativa", "section": "rendición"}
        }
    ]
    
    # Guardar chunks de ejemplo
    chunks_file = "data/processed/sample_chunks.json"
    with open(chunks_file, "w", encoding="utf-8") as f:
        json.dump(sample_chunks, f, ensure_ascii=False, indent=2)
    print(f"  ✓ Datos de ejemplo creados: {chunks_file}")


def create_config() -> None:
    """Crear archivo de configuración."""
    print("⚙️ Creando archivo de configuración...")
    
    config = {
        "paths": {
            "chunks": "data/processed/chunks.json",
            "vectorstores": {
                "tfidf": "data/vectorstores/tfidf.pkl",
                "bm25": "data/vectorstores/bm25.pkl",
                "transformers": "data/vectorstores/transformers.pkl"
            }
        },
        "models": {
            "transformer_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "spacy_model": "es_core_news_sm"
        },
        "search": {
            "default_top_k": 5,
            "fusion_strategy": "weighted"
        },
        "logging": {
            "level": "INFO",
            "file_logging": True
        }
    }
    
    config_file = "config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Configuración creada: {config_file}")


def create_demo_script() -> None:
    """Crear script de demostración."""
    print("🎯 Creando script de demostración...")
    
    demo_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo del Sistema de Búsqueda Híbrido MINEDU

Uso: python demo.py "tu consulta aquí"
"""
import sys
from src.core.hybrid import HybridSearch

def main():
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("Uso: python demo.py 'tu consulta aquí'")
        print("Ejemplo: python demo.py '¿Cuál es el monto máximo para viáticos?'")
        return
    
    query = " ".join(sys.argv[1:])
    
    print(f"\\n🔍 Buscando: {query}")
    print("-" * 50)
    
    try:
        # Inicializar búsqueda híbrida
        searcher = HybridSearch(
            bm25_vectorstore_path="data/vectorstores/bm25.pkl",
            tfidf_vectorstore_path="data/vectorstores/tfidf.pkl",
            transformer_vectorstore_path="data/vectorstores/transformers.pkl"
        )
        
        # Realizar búsqueda
        results = searcher.search(query, top_k=3)
        
        # Mostrar resultados
        print(f"\\n📊 Encontrados {len(results)} resultados:\\n")
        
        for i, result in enumerate(results, 1):
            print(f"{i}. Score: {result['score']:.3f}")
            print(f"   {result['texto'][:200]}...")
            print(f"   Método: {result.get('method', 'Híbrido')}")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Asegúrate de que los vectorstores estén generados primero.")

if __name__ == "__main__":
    main()
'''
    
    with open("demo.py", "w", encoding="utf-8") as f:
        f.write(demo_content)
    print("  ✓ Script de demostración creado: demo.py")


def create_makefile() -> None:
    """Crear Makefile para comandos comunes."""
    print("🔧 Creando Makefile...")
    
    makefile_content = '''# Makefile para el Sistema de Búsqueda Híbrido MINEDU

.PHONY: install setup test clean run-demo format

install:
	pip install -r requirements.txt
	python -m spacy download es_core_news_sm

setup:
	python setup_project.py

test:
	pytest tests/ -v

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -delete

run-demo:
	python demo.py "¿Cuál es el monto máximo para viáticos?"

format:
	black src/ tests/
	flake8 src/ tests/

generate-vectorstores:
	python src/data_pipeline/generate_vectorstores.py

full-setup: install setup generate-vectorstores
'''
    
    with open("Makefile", "w", encoding="utf-8") as f:
        f.write(makefile_content)
    print("  ✓ Makefile creado: Makefile")


def create_requirements() -> None:
    """Crear archivo requirements.txt unificado."""
    print("📦 Creando requirements.txt...")
    
    requirements = '''# Core dependencies
numpy==1.24.3
scikit-learn==1.3.0
pandas==2.0.3

# Search algorithms
rank-bm25==0.2.2
sentence-transformers==2.2.2

# Text processing
spacy==3.6.0
nltk==3.8.1

# PDF processing
PyMuPDF==1.23.0

# Utilities
python-dotenv==1.0.0
tqdm==4.65.0

# Testing
pytest==7.4.0
pytest-cov==4.1.0

# Development
black==23.7.0
flake8==6.1.0
'''
    
    with open("requirements.txt", "w", encoding="utf-8") as f:
        f.write(requirements)
    print("  ✓ Requirements.txt creado")


def create_test_structure() -> None:
    """Crear estructura básica de tests."""
    print("🧪 Creando estructura de tests...")
    
    # Crear archivo __init__.py para tests
    test_init = '''"""
Test suite for MINEDU Document Search System.
"""
'''
    
    with open("tests/__init__.py", "w", encoding="utf-8") as f:
        f.write(test_init)
    
    # Crear test básico
    test_content = '''#!/usr/bin/env python3
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
'''
    
    with open("tests/test_retrieval.py", "w", encoding="utf-8") as f:
        f.write(test_content)
    
    print("  ✓ Estructura de tests creada")


def main() -> None:
    """Función principal de configuración."""
    print("🚀 CONFIGURACIÓN DEL PROYECTO MINEDU DOCUMENT SEARCH SYSTEM")
    print("=" * 60)
    
    try:
        setup_directories()
        download_sample_data()
        create_config()
        create_demo_script()
        create_makefile()
        create_requirements()
        create_test_structure()
        
        print("\n✅ PROYECTO CONFIGURADO CORRECTAMENTE")
        print("=" * 60)
        print("📋 Próximos pasos:")
        print("  1. Instalar dependencias: pip install -r requirements.txt")
        print("  2. Generar vectorstores: python src/data_pipeline/generate_vectorstores.py")
        print("  3. Ejecutar demo: python demo.py '¿Cuál es el monto máximo para viáticos?'")
        print("  4. Ejecutar tests: pytest tests/")
        print("\n💡 También puedes usar: make full-setup")
        
    except Exception as e:
        print(f"\n❌ Error durante la configuración: {e}")
        raise


if __name__ == "__main__":
    main() 