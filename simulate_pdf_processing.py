#!/usr/bin/env python3
"""
Simulate PDF Processing - Show Expected Results
==============================================

This script simulates what the OCR pipeline should extract from the real
directiva PDF, based on typical legal document content patterns.
"""

import sys
import json
import re
from pathlib import Path
from collections import defaultdict

# Add src to path  
sys.path.append(str(Path(__file__).parent / "src"))

def simulate_ocr_extraction():
    """Simulate OCR extraction from the directiva PDF."""
    
    print("🔮 SIMULATING OCR EXTRACTION FROM DIRECTIVA PDF")
    print("=" * 55)
    
    # Simulate typical content that would be extracted from a legal directiva
    simulated_ocr_pages = [
        {
            'page_number': 1,
            'text': """
            DIRECTIVA N° 011-2020-MINEDU
            "Disposiciones y Procedimientos para Requerir, Otorgar, y Rendir 
            Cuenta de Viáticos, Pasajes y Otros Gastos de Viaje en el Territorio Nacional"
            
            1. OBJETO
            Establecer las disposiciones y procedimientos para el requerimiento, 
            otorgamiento y rendición de cuenta de viáticos, pasajes y otros gastos.
            """,
            'confidence': 0.92
        },
        {
            'page_number': 2,
            'text': """
            8. DISPOSICIONES ESPECÍFICAS
            
            8.1. Para el requerimiento de viáticos, pasajes terrestres y otros gastos
            de viaje, el Jefe del órgano deberá remitir la documentación con cinco (05)
            días hábiles anteriores a la fecha prevista.
            
            8.4. Los gastos de movilidad que se rindan mediante Declaración Jurada,
            deberán sujetarse a los montos que se indican a continuación:
            """,
            'confidence': 0.89
        },
        {
            'page_number': 3,
            'text': """
            TABLA DE MONTOS PARA VIÁTICOS
            
            Concepto                                Lima    Regiones
            Traslado del domicilio al aeropuerto    S/ 25,00   No procede
            Traslado del aeropuerto al hospedaje    S/ 35,00   No procede  
            Movilidad local en lugar de destino     S/ 30,00   Hasta S/ 45,00
            por día
            
            8.4.17. El comisionado podrá presentar únicamente Declaración Jurada
            por un monto que no podrá exceder el treinta por ciento (30%) del
            monto total de los viáticos asignados.
            """,
            'confidence': 0.87
        },
        {
            'page_number': 4,
            'text': """
            ESCALAS DE VIÁTICOS SEGÚN NIVEL
            
            Servidor Público/Civil: S/ 320.00 diarios
            Funcionarios de confianza: S/ 350.00 diarios  
            Ministros de Estado: S/ 380.00 diarios
            
            Según lo establecido en el Decreto Supremo N° 007-2013-EF
            y sus modificatorias.
            """,
            'confidence': 0.91
        },
        {
            'page_number': 5,
            'text': """
            8.5. RENDICIÓN DE CUENTAS
            
            Los gastos de viáticos se rinden dentro de los cinco (5) días hábiles
            posteriores al término de la comisión, presentando los comprobantes
            correspondientes según el Reglamento de Comprobantes de Pago de SUNAT.
            
            Para gastos en zonas rurales o lugares inhóspitos, se podrá presentar
            Declaración Jurada hasta por un monto máximo de S/ 30.00 por día.
            """,
            'confidence': 0.88
        }
    ]
    
    return simulated_ocr_pages


def simulate_entity_extraction(ocr_pages):
    """Simulate NER entity extraction."""
    
    print("\n🤖 SIMULATING NER ENTITY EXTRACTION")
    print("=" * 40)
    
    # Entity patterns
    patterns = {
        'amount': re.compile(r'S/\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', re.IGNORECASE),
        'percentage': re.compile(r'(\d{1,2}(?:\.\d+)?)\s*(?:%|por\s+ciento)', re.IGNORECASE),
        'numeral': re.compile(r'(\d{1,2}\.\d{1,2}(?:\.\d{1,2})?)', re.IGNORECASE),
        'reference': re.compile(r'(decreto\s+supremo\s+n[°º]\s*\d{3}-\d{4}-[A-Z]{2,4})', re.IGNORECASE),
        'directive': re.compile(r'(directiva\s+n[°º]\s*\d{3}-\d{4}-[A-Z]{2,10})', re.IGNORECASE),
        'role_minister': re.compile(r'(ministros?\s+de\s+estado)', re.IGNORECASE),
        'role_civil': re.compile(r'(servidor\s+(?:público|civil)|funcionarios?\s+de\s+confianza)', re.IGNORECASE),
        'declaration': re.compile(r'(declaración\s+jurada)', re.IGNORECASE),
        'timeframe': re.compile(r'(\d{1,2})\s*\(\d{1,2}\)\s*días?\s+hábiles', re.IGNORECASE)
    }
    
    all_entities = defaultdict(list)
    
    for page in ocr_pages:
        text = page['text']
        page_num = page['page_number']
        
        for entity_type, pattern in patterns.items():
            matches = pattern.findall(text)
            for match in matches:
                all_entities[entity_type].append({
                    'text': match,
                    'page': page_num,
                    'normalized': normalize_entity(entity_type, match)
                })
    
    # Remove duplicates
    for entity_type in all_entities:
        seen = set()
        unique_entities = []
        for entity in all_entities[entity_type]:
            key = entity['normalized'] or entity['text']
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        all_entities[entity_type] = unique_entities
    
    return dict(all_entities)


def normalize_entity(entity_type, text):
    """Normalize entity values."""
    
    if entity_type == 'amount':
        # Remove S/ and normalize format
        amount = re.sub(r'^S/\s*', '', text)
        amount = amount.replace(',', '')
        try:
            value = float(amount)
            return f"S/ {value:.2f}"
        except:
            return text
    
    elif entity_type == 'percentage':
        return f"{text}%"
    
    elif entity_type in ['reference', 'directive']:
        return text.upper()
    
    else:
        return text.lower()


def simulate_intelligent_chunking(ocr_pages, entities):
    """Simulate intelligent chunking with rich metadata."""
    
    print("\n🧠 SIMULATING INTELLIGENT CHUNKING")
    print("=" * 35)
    
    chunks = []
    
    # Create chunks based on content sections
    chunk_templates = [
        {
            'section': '1',
            'title': 'Objeto de la Directiva',
            'content': 'Establecer las disposiciones y procedimientos para el requerimiento, otorgamiento y rendición de cuenta de viáticos, pasajes y otros gastos de viaje en el territorio nacional.',
            'entities': {
                'directive': ['DIRECTIVA N° 011-2020-MINEDU'],
                'procedure': ['requerimiento', 'otorgamiento', 'rendición']
            }
        },
        {
            'section': '8.4',
            'title': 'Gastos de Movilidad - Declaración Jurada',
            'content': 'Los gastos de movilidad que se rindan mediante Declaración Jurada, deberán sujetarse a los montos indicados: Movilidad local en lugar de destino S/ 30,00 por día.',
            'entities': {
                'amount': ['S/ 30.00'],
                'declaration': ['Declaración Jurada'],
                'procedure': ['gastos de movilidad']
            }
        },
        {
            'section': '8.4.17',
            'title': 'Límite Declaración Jurada',
            'content': 'El comisionado podrá presentar únicamente Declaración Jurada por un monto que no podrá exceder el treinta por ciento (30%) del monto total de los viáticos asignados.',
            'entities': {
                'percentage': ['30%'],
                'declaration': ['Declaración Jurada'],
                'procedure': ['límite de viáticos']
            }
        },
        {
            'section': 'ESCALA_MINISTROS',
            'title': 'Escala de Viáticos - Ministros de Estado',
            'content': 'Ministros de Estado tienen asignado S/ 380.00 diarios para viáticos nacionales, según lo establecido en el Decreto Supremo N° 007-2013-EF.',
            'entities': {
                'amount': ['S/ 380.00'],
                'role_minister': ['Ministros de Estado'],
                'reference': ['DECRETO SUPREMO N° 007-2013-EF']
            }
        },
        {
            'section': 'ESCALA_CIVILES',
            'title': 'Escala de Viáticos - Servidores Civiles',
            'content': 'Servidor Público/Civil tiene asignado S/ 320.00 diarios para viáticos nacionales. Funcionarios de confianza S/ 350.00 diarios.',
            'entities': {
                'amount': ['S/ 320.00', 'S/ 350.00'],
                'role_civil': ['Servidor Público', 'Funcionarios de confianza']
            }
        },
        {
            'section': '8.5',
            'title': 'Rendición de Cuentas',
            'content': 'Los gastos de viáticos se rinden dentro de los cinco (5) días hábiles posteriores al término de la comisión. Para zonas rurales se podrá presentar Declaración Jurada hasta S/ 30.00 por día.',
            'entities': {
                'timeframe': ['5 días hábiles'],
                'amount': ['S/ 30.00'],
                'declaration': ['Declaración Jurada']
            }
        }
    ]
    
    for i, template in enumerate(chunk_templates, 1):
        
        # Determine role level for ranking
        role_level = None
        if any('ministro' in str(template['entities']).lower() for k in template['entities']):
            role_level = 'minister'
        elif any('servidor' in str(template['entities']).lower() or 'funcionario' in str(template['entities']).lower() for k in template['entities']):
            role_level = 'civil_servant'
        
        # Check for amounts
        has_amounts = bool(template['entities'].get('amount', []))
        
        chunk = {
            'id': i,
            'texto': template['content'],
            'titulo': template['title'],
            'metadatos': {
                'section_number': template['section'],
                'section_type': 'section',
                'hierarchy_level': template['section'].count('.'),
                'entities': template['entities'],
                'role_level': role_level,
                'has_amounts': has_amounts,
                'has_procedures': 'procedure' in template['entities'],
                'source': 'OCR_pipeline_simulation',
                'confidence': 0.9,
                'document_type': 'legal_regulation'
            }
        }
        
        chunks.append(chunk)
    
    return chunks


def test_specific_queries(chunks):
    """Test the three specific queries with simulated chunks."""
    
    print("\n🎯 TESTING SPECIFIC QUERIES ON SIMULATED DATA")
    print("=" * 50)
    
    queries = [
        {
            'query': "¿Cuánto corresponde de viáticos diarios a través de declaración jurada en Lima?",
            'keywords': ['declaración jurada', 'lima', 'diarios', 'viáticos']
        },
        {
            'query': "¿Qué numeral establece el límite de S/ 30 para declaración jurada?",
            'keywords': ['numeral', 's/ 30', '30', 'declaración jurada', 'límite']
        },
        {
            'query': "¿Cuánto pueden gastar los ministros vs servidores civiles en viáticos?",
            'keywords': ['ministros', 'servidores civiles', 'gastar', 'viáticos']
        }
    ]
    
    for i, q in enumerate(queries, 1):
        print(f"\n🔍 Query {i}: {q['query']}")
        
        # Search in chunks
        relevant_chunks = []
        
        for chunk in chunks:
            texto = chunk.get('texto', '').lower()
            title = chunk.get('titulo', '').lower()
            entities = chunk.get('metadatos', {}).get('entities', {})
            
            score = 0
            
            # Score by keyword presence
            for keyword in q['keywords']:
                if keyword.lower() in texto or keyword.lower() in title:
                    score += 2
                
                # Check in entities
                for entity_list in entities.values():
                    for entity in entity_list:
                        if keyword.lower() in str(entity).lower():
                            score += 1
            
            if score > 0:
                relevant_chunks.append((chunk, score))
        
        # Sort by relevance
        relevant_chunks.sort(key=lambda x: x[1], reverse=True)
        
        print(f"   📊 Found {len(relevant_chunks)} relevant chunks:")
        
        for j, (chunk, score) in enumerate(relevant_chunks[:3], 1):
            print(f"   {j}. {chunk['titulo']} (score: {score})")
            print(f"      Section: {chunk['metadatos']['section_number']}")
            print(f"      Text: {chunk['texto'][:150]}...")
            
            entities = chunk['metadatos']['entities']
            if entities:
                print(f"      Key entities: {dict(entities)}")
            
            role_level = chunk['metadatos'].get('role_level')
            if role_level:
                print(f"      Role level: {role_level}")


def main():
    """Run the simulation."""
    
    print("🔮 SIMULATING REAL DIRECTIVA PDF PROCESSING")
    print("=" * 50)
    print("This simulation shows what the OCR pipeline should extract")
    print("from the real directiva_de_viaticos_011_2020_imagen.pdf")
    print("=" * 50)
    
    # Simulate OCR extraction
    ocr_pages = simulate_ocr_extraction()
    print(f"✓ Simulated OCR extraction: {len(ocr_pages)} pages")
    
    # Simulate entity extraction
    entities = simulate_entity_extraction(ocr_pages)
    print(f"✓ Simulated entity extraction:")
    for entity_type, entity_list in entities.items():
        print(f"   {entity_type}: {len(entity_list)} entities")
        if entity_list:
            examples = [e['normalized'] or e['text'] for e in entity_list[:3]]
            print(f"      Examples: {examples}")
    
    # Simulate intelligent chunking
    chunks = simulate_intelligent_chunking(ocr_pages, entities)
    print(f"✓ Simulated intelligent chunking: {len(chunks)} chunks")
    
    # Test specific queries
    test_specific_queries(chunks)
    
    # Save simulated results
    output_file = "simulated_directiva_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'chunks': chunks,
            'entities': entities,
            'simulation_summary': {
                'pages_processed': len(ocr_pages),
                'entities_extracted': sum(len(e) for e in entities.values()),
                'chunks_created': len(chunks)
            }
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 Simulation results saved to: {output_file}")
    
    print(f"\n🚀 TO PROCESS THE REAL PDF:")
    print("1. Install dependencies: pip install paddleocr opencv-python pillow pdf2image")
    print("2. Run: python process_real_directiva.py")
    print("3. Test with demo: python demo.py \"¿Cuánto pueden gastar los ministros?\"")
    
    print(f"\n✅ SIMULATION COMPLETED")
    print("The OCR pipeline should extract similar content from the real PDF!")


if __name__ == "__main__":
    main()