#!/usr/bin/env python3
"""
Verificación Rápida de S/ 380 en PDF
===================================

Script para confirmar que S/ 380 existe en el PDF y mostrar su ubicación.
"""

import fitz
import re

def verify_380_in_pdf(pdf_path: str = 'data/raw/directiva_de_viaticos_011_2020_imagen.pdf'):
    """Verificar presencia de 380 en el PDF"""
    
    print(f"🔍 Verificando presencia de '380' en: {pdf_path}")
    print("=" * 60)
    
    try:
        pdf = fitz.open(pdf_path)
        found_instances = []
        
        for page_num in range(len(pdf)):
            page = pdf.load_page(page_num)
            text = page.get_text()
            
            # Buscar diferentes variaciones de 380
            patterns = [
                r'S/\s*380',
                r'380[,\.]00',
                r'\b380\b',
                r'trescientos\s+ochenta',
                r'TRESCIENTOS\s+OCHENTA'
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    # Extraer contexto
                    start = max(0, match.start() - 100)
                    end = min(len(text), match.end() + 100)
                    context = text[start:end].strip()
                    
                    found_instances.append({
                        'page': page_num + 1,
                        'match': match.group(0),
                        'pattern': pattern,
                        'context': context
                    })
                    
                    print(f"✅ '{match.group(0)}' encontrado en página {page_num + 1}")
                    print(f"   Patrón: {pattern}")
                    print(f"   Contexto: ...{context[:100]}...")
                    print()
        
        pdf.close()
        
        print(f"📊 RESUMEN:")
        print(f"   Total instancias encontradas: {len(found_instances)}")
        
        if found_instances:
            print(f"   ✅ S/ 380 EXISTE en el PDF")
            print(f"   📍 Páginas: {sorted(set(inst['page'] for inst in found_instances))}")
        else:
            print(f"   ❌ S/ 380 NO encontrado en el PDF")
        
        return found_instances
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

if __name__ == '__main__':
    verify_380_in_pdf() 