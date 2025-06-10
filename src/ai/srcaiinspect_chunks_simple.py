#!/usr/bin/env python3
"""
Script simple para inspeccionar los chunks y buscar términos específicos
"""

import json
from pathlib import Path

# Ruta del archivo de chunks
PROJECT_ROOT = Path(__file__).parent.parent.parent
CHUNKS_FILE = PROJECT_ROOT / "data" / "processed" / "chunks_directiva_limpia.json"

def search_in_chunks(search_term):
    """Busca un término específico en todos los chunks"""
    try:
        with open(CHUNKS_FILE, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        print(f"🔍 Buscando '{search_term}' en {len(chunks)} chunks...")
        print("=" * 60)
        
        found_chunks = []
        
        for chunk in chunks:
            text = chunk['text'].lower()
            if search_term.lower() in text:
                found_chunks.append(chunk)
                print(f"✅ ENCONTRADO en Chunk {chunk['chunk_index']}")
                print(f"📄 Páginas: {chunk['pages']}")
                print(f"📝 Texto (primeros 300 caracteres):")
                print(f"   {chunk['text'][:300]}...")
                print("-" * 50)
        
        if not found_chunks:
            print(f"❌ No se encontró '{search_term}' en ningún chunk")
            print("\n💡 Sugerencias:")
            print("- Prueba términos más generales")
            print("- Busca palabras clave relacionadas")
            print("- El término puede estar escrito diferente")
        
        return found_chunks
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return []

def show_all_chunks_preview():
    """Muestra un preview de todos los chunks"""
    try:
        with open(CHUNKS_FILE, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        print(f"📋 PREVIEW DE TODOS LOS CHUNKS ({len(chunks)} total)")
        print("=" * 60)
        
        for chunk in chunks:
            print(f"🔹 Chunk {chunk['chunk_index']} | Páginas: {chunk['pages']} | Palabras: {chunk['word_count']}")
            # Mostrar las primeras 100 palabras para buscar patrones
            words = chunk['text'].split()[:30]
            preview = ' '.join(words) + "..."
            print(f"   {preview}")
            print("-" * 40)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def main():
    """Función principal de inspección"""
    print("🔍 INSPECTOR DE CHUNKS - DIRECTIVA LIMPIA")
    print("=" * 50)
    
    # Buscar términos específicos
    search_terms = [
        "320",
        "trescientos",
        "viático",
        "viáticos", 
        "monto",
        "máximo",
        "límite",
        "S/",
        "soles",
        "responsabilidades",
        "responsabilidad"
    ]
    
    for term in search_terms:
        print(f"\n🔍 Buscando: '{term}'")
        results = search_in_chunks(term)
        if results:
            print(f"✅ Encontrado en {len(results)} chunks")
        else:
            print(f"❌ No encontrado")
    
    print("\n" + "=" * 60)
    print("📋 ¿Quieres ver el preview completo de todos los chunks? (s/n)")
    
    response = input().strip().lower()
    if response in ['s', 'si', 'yes', 'y']:
        print("\n")
        show_all_chunks_preview()

if __name__ == "__main__":
    main()