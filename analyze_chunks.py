#!/usr/bin/env python3
"""
Análisis de chunks para encontrar los montos de viáticos
"""

import json
import re

def analyze_chunks():
    """Analizar chunks para encontrar montos"""
    print("🔍 ANÁLISIS DE CHUNKS - BÚSQUEDA DE MONTOS")
    print("=" * 50)
    
    try:
        # Leer chunks con encoding correcto
        with open('data/processed/chunks_directiva_limpia.json', 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        print(f"📊 Total de chunks: {len(chunks)}")
        
        # Buscar montos específicos
        target_amounts = ['380', '320', '30']
        found_amounts = {amount: [] for amount in target_amounts}
        
        for i, chunk in enumerate(chunks):
            text = chunk['text']
            
            # Buscar cada monto
            for amount in target_amounts:
                if amount in text:
                    found_amounts[amount].append(i)
        
        print("\n💰 MONTOS ENCONTRADOS:")
        for amount, chunk_ids in found_amounts.items():
            print(f"   S/ {amount}: Chunks {chunk_ids}")
        
        # Análisis detallado del chunk que contiene la escala
        print("\n📋 ANÁLISIS DETALLADO - CHUNK CON ESCALA:")
        
        for i, chunk in enumerate(chunks):
            if 'ESCALA DE VIÁTICOS' in chunk['text'] or '320' in chunk['text']:
                print(f"\n🎯 CHUNK {i}:")
                print("=" * 30)
                
                # Extraer líneas relevantes
                lines = chunk['text'].split('\n')
                for j, line in enumerate(lines):
                    line_clean = line.strip()
                    if any(keyword in line_clean.upper() for keyword in 
                           ['ESCALA', '320', '380', 'MINISTRO', 'SERVIDOR', 'VIÁTICO']):
                        print(f"   Línea {j}: {line_clean[:100]}")
                
                # Buscar tabla específica
                print("\n🔍 BÚSQUEDA DE TABLA:")
                table_pattern = r'(\d+,\d+)\s+(.*?)(?=\n|$)'
                matches = re.findall(table_pattern, chunk['text'])
                for match in matches:
                    amount, description = match
                    print(f"   💰 {amount} - {description.strip()[:80]}")
        
        # Verificar si falta información
        print("\n❌ PROBLEMAS DETECTADOS:")
        
        if not found_amounts['380']:
            print("   • NO se encontró el monto S/ 380.00 para ministros")
        if not found_amounts['320']:
            print("   • NO se encontró el monto S/ 320.00 para servidores")
        if not found_amounts['30']:
            print("   • NO se encontró el límite S/ 30.00 para declaración jurada")
        
        # Recomendaciones
        print("\n✅ RECOMENDACIONES:")
        if not any(found_amounts.values()):
            print("   1. El PDF original tiene problemas de extracción OCR")
            print("   2. Los chunks no contienen la información completa")
            print("   3. Se necesita reprocesar el PDF con mejor OCR")
        else:
            print("   1. Algunos montos se encuentran, verificar chunking")
            print("   2. Optimizar el algoritmo de extracción")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al analizar chunks: {e}")
        return False

def search_in_text():
    """Buscar texto específico en los chunks"""
    print("\n🔍 BÚSQUEDA DE TEXTO ESPECÍFICO:")
    print("-" * 40)
    
    search_terms = [
        "380",
        "Ministro",
        "Viceministro", 
        "Secretario General",
        "320",
        "servidor civil",
        "30",
        "declaración jurada"
    ]
    
    try:
        with open('data/processed/chunks_directiva_limpia.json', 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        for term in search_terms:
            found_in = []
            for i, chunk in enumerate(chunks):
                if term.lower() in chunk['text'].lower():
                    found_in.append(i)
            
            if found_in:
                print(f"✅ '{term}': Chunks {found_in}")
            else:
                print(f"❌ '{term}': NO encontrado")
    
    except Exception as e:
        print(f"❌ Error en búsqueda: {e}")

def main():
    """Función principal"""
    success = analyze_chunks()
    search_in_text()
    
    print("\n" + "=" * 50)
    if success:
        print("🎯 CONCLUSIÓN:")
        print("El sistema tiene problemas de extracción de la información clave.")
        print("Los montos específicos (S/ 380, S/ 320, S/ 30) no están")
        print("siendo capturados correctamente en los chunks.")
        print("\n💡 SOLUCIÓN:")
        print("1. Reprocesar el PDF con mejor OCR")
        print("2. Verificar la tabla de escala de viáticos")
        print("3. Mejorar el chunking para capturar tablas")
    else:
        print("❌ No se pudo completar el análisis")

if __name__ == "__main__":
    main() 