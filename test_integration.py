#!/usr/bin/env python3
"""
Test de integración para diagnosticar problema LangGraph 503
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_retriever():
    """Test 1: SimpleRetriever standalone"""
    print("🔍 TEST 1: SimpleRetriever standalone...")
    try:
        from backend.src.langchain_integration.vectorstores.simple_retriever import retriever
        
        stats = retriever.get_stats()
        print(f"✅ Retriever loaded: {stats['total_documents']} documents")
        
        # Test search
        results = retriever.simple_similarity_search("monto viáticos", k=3)
        print(f"✅ Search works: {len(results)} results found")
        
        if results:
            first_result = results[0].page_content[:100]
            print(f"✅ First result: {first_result}...")
        
        return True
    except Exception as e:
        print(f"❌ Retriever failed: {e}")
        return False

def test_professional_langgraph():
    """Test 2: Professional LangGraph import"""
    print("\n🔍 TEST 2: Professional LangGraph import...")
    try:
        from backend.src.langchain_integration.orchestration.professional_langgraph import professional_orchestrator
        print("✅ Professional LangGraph imported successfully")
        return True
    except Exception as e:
        print(f"❌ Professional LangGraph failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """Test 3: Config loading"""
    print("\n🔍 TEST 3: Config loading...")
    try:
        from backend.src.langchain_integration.config import config
        print(f"✅ Config loaded: {type(config)}")
        return True
    except Exception as e:
        print(f"❌ Config failed: {e}")
        return False

def test_backend_import():
    """Test 4: Backend main.py imports"""
    print("\n🔍 TEST 4: Backend main.py imports...")
    try:
        # Simulate backend imports
        sys.path.insert(0, str(project_root / "backend" / "src"))
        
        print("  - Testing LangGraph imports...")
        from langchain_integration.orchestration.professional_langgraph import professional_orchestrator
        print("  ✅ professional_orchestrator imported")
        
        from langchain_integration.vectorstores.simple_retriever import retriever
        print("  ✅ retriever imported")
        
        return True
    except Exception as e:
        print(f"  ❌ Backend imports failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def diagnose_503_error():
    """Diagnose specific 503 error"""
    print("\n🚨 DIAGNÓSTICO ERROR 503:")
    
    # Check paths
    print("📁 Checking paths...")
    chunks_path = project_root / "data" / "processed" / "chunks.json"
    print(f"  - chunks.json exists: {chunks_path.exists()}")
    
    if chunks_path.exists():
        import json
        with open(chunks_path) as f:
            chunks = json.load(f)
        print(f"  - chunks count: {len(chunks)}")
    
    # Check missing dependencies
    print("\n📦 Checking dependencies...")
    try:
        import langchain
        print(f"  ✅ langchain: {langchain.__version__}")
    except ImportError:
        print("  ❌ langchain not installed")
    
    try:
        import langgraph
        print(f"  ✅ langgraph: {langgraph.__version__}")
    except ImportError:
        print("  ❌ langgraph not installed")
    
    try:
        import openai
        print(f"  ✅ openai: {openai.__version__}")
    except ImportError:
        print("  ❌ openai not installed")

if __name__ == "__main__":
    print("🔧 DIAGNÓSTICO DE INTEGRACIÓN LANGGRAPH\n")
    
    # Run tests
    test1_ok = test_retriever()
    test2_ok = test_professional_langgraph()
    test3_ok = test_config()
    test4_ok = test_backend_import()
    
    # Diagnose
    diagnose_503_error()
    
    # Summary
    print(f"\n📊 RESUMEN:")
    print(f"  - Retriever: {'✅' if test1_ok else '❌'}")
    print(f"  - LangGraph: {'✅' if test2_ok else '❌'}")
    print(f"  - Config: {'✅' if test3_ok else '❌'}")
    print(f"  - Backend imports: {'✅' if test4_ok else '❌'}")
    
    if all([test1_ok, test2_ok, test3_ok, test4_ok]):
        print("\n✅ TODOS LOS TESTS PASARON - Error 503 podría ser de runtime")
    else:
        print("\n❌ PROBLEMAS DETECTADOS - Revisar imports faltantes")