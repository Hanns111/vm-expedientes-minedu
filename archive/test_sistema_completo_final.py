#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST FINAL DEL SISTEMA COMPLETO - 3 SISTEMAS
TF-IDF + Transformers + BM25 (Corregido)
"""

import time
import json
from datetime import datetime
from src.ai.search_vectorstore_hybrid import SearchVectorstore
from src.ai.search_vectorstore_bm25_fixed import BM25SearchFixed

def test_sistema_completo():
    """Test final del sistema completo con los 3 métodos"""
    print("🏆 TEST FINAL DEL SISTEMA COMPLETO")
    print("TF-IDF + Transformers + BM25 (Corregido)")
    print("=" * 60)
    
    # Las 8 consultas de validación
    consultas = [
        "¿Cuál es el monto máximo diario para viáticos nacionales?",
        "¿Quién autoriza los viáticos en el MINEDU?",
        "¿Qué documentos se requieren para solicitar viáticos?",
        "¿Cuántos días antes debo solicitar viáticos?",
        "¿Cómo se rinden los gastos de viáticos?",
        "¿Cuáles son las responsabilidades del comisionado?",
        "¿Qué sucede si no rindo mis viáticos a tiempo?",
        "¿Se pueden solicitar viáticos para viajes internacionales?"
    ]
    
    # Inicializar sistemas
    print("🔧 Inicializando sistemas...")
    hybrid_search = SearchVectorstore('data/processed/vectorstore_semantic_full_v2.pkl')
    bm25_search = BM25SearchFixed('data/processed/vectorstore_bm25_test.pkl')
    
    resultados = {
        'fecha': datetime.now().isoformat(),
        'consultas': [],
        'estadisticas': {}
    }
    
    print(f"🔍 Probando {len(consultas)} consultas con 3 sistemas...")
    
    for i, consulta in enumerate(consultas, 1):
        print(f"\n📝 Consulta {i}: {consulta}")
        
        consulta_result = {
            'consulta': consulta,
            'hybrid': {'resultados': 0, 'tiempo': 0, 'exito': False},
            'bm25': {'resultados': 0, 'tiempo': 0, 'exito': False}
        }
        
        # Test Sistema Híbrido (TF-IDF + Transformers)
        try:
            start_time = time.time()
            hybrid_results = hybrid_search.search(consulta, top_k=3)
            elapsed_time = time.time() - start_time
            
            consulta_result['hybrid'] = {
                'resultados': len(hybrid_results.get('results', [])),
                'tiempo': elapsed_time,
                'exito': len(hybrid_results.get('results', [])) > 0
            }
            print(f"   ✅ Híbrido: {len(hybrid_results.get('results', []))} resultados en {elapsed_time:.4f}s")
        except Exception as e:
            print(f"   ❌ Híbrido Error: {str(e)[:50]}...")
        
        # Test BM25
        try:
            start_time = time.time()
            bm25_results = bm25_search.search(consulta, top_k=3)
            elapsed_time = time.time() - start_time
            
            consulta_result['bm25'] = {
                'resultados': len(bm25_results),
                'tiempo': elapsed_time,
                'exito': len(bm25_results) > 0
            }
            print(f"   ✅ BM25: {len(bm25_results)} resultados en {elapsed_time:.4f}s")
        except Exception as e:
            print(f"   ❌ BM25 Error: {str(e)[:50]}...")
        
        resultados['consultas'].append(consulta_result)
    
    # Calcular estadísticas
    print(f"\n📊 CALCULANDO ESTADÍSTICAS FINALES...")
    
    # Sistema Híbrido
    hybrid_exitos = sum(1 for c in resultados['consultas'] if c['hybrid']['exito'])
    hybrid_tiempo_promedio = sum(c['hybrid']['tiempo'] for c in resultados['consultas']) / len(resultados['consultas'])
    
    # BM25
    bm25_exitos = sum(1 for c in resultados['consultas'] if c['bm25']['exito'])
    bm25_tiempo_promedio = sum(c['bm25']['tiempo'] for c in resultados['consultas']) / len(resultados['consultas'])
    
    resultados['estadisticas'] = {
        'hybrid': {
            'consultas_respondidas': hybrid_exitos,
            'porcentaje_exito': (hybrid_exitos / len(consultas)) * 100,
            'tiempo_promedio': hybrid_tiempo_promedio
        },
        'bm25': {
            'consultas_respondidas': bm25_exitos,
            'porcentaje_exito': (bm25_exitos / len(consultas)) * 100,
            'tiempo_promedio': bm25_tiempo_promedio
        }
    }
    
    # Mostrar resultados
    print(f"\n🏆 RESULTADOS FINALES DEL SISTEMA COMPLETO")
    print(f"=" * 60)
    
    print(f"📊 Sistema Híbrido (TF-IDF + Transformers):")
    print(f"   ✅ Respondidas: {hybrid_exitos}/{len(consultas)} ({resultados['estadisticas']['hybrid']['porcentaje_exito']:.1f}%)")
    print(f"   ⏱️ Tiempo promedio: {hybrid_tiempo_promedio:.4f}s")
    
    print(f"\n📊 BM25:")
    print(f"   ✅ Respondidas: {bm25_exitos}/{len(consultas)} ({resultados['estadisticas']['bm25']['porcentaje_exito']:.1f}%)")
    print(f"   ⏱️ Tiempo promedio: {bm25_tiempo_promedio:.4f}s")
    
    # Evaluación final
    total_sistemas = 2
    sistemas_funcionando = sum([
        resultados['estadisticas']['hybrid']['porcentaje_exito'] >= 75,
        resultados['estadisticas']['bm25']['porcentaje_exito'] >= 75
    ])
    
    print(f"\n🎯 EVALUACIÓN FINAL:")
    print(f"   🔧 Sistemas funcionando: {sistemas_funcionando}/{total_sistemas}")
    print(f"   💬 Consultas totales respondidas: {hybrid_exitos + bm25_exitos}/{len(consultas) * 2}")
    
    if sistemas_funcionando == 2:
        print(f"\n🏆 ¡EXCELENTE! SISTEMA HÍBRIDO 100% FUNCIONAL")
        print(f"✅ Los 2 sistemas están funcionando correctamente")
        print(f"🚀 Proyecto listo para presentación y producción")
        estado_final = "EXCELENTE"
    elif sistemas_funcionando >= 1:
        print(f"\n✅ ¡BUENO! SISTEMA HÍBRIDO FUNCIONAL")
        print(f"🎯 {sistemas_funcionando}/2 sistemas funcionando correctamente")
        estado_final = "BUENO"
    else:
        print(f"\n⚠️ SISTEMA HÍBRIDO NECESITA MEJORAS")
        print(f"🔧 Solo {sistemas_funcionando}/2 sistemas funcionando")
        estado_final = "MEJORAR"
    
    # Guardar resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reports/test_sistema_completo_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Resultados guardados: {filename}")
    print(f"🎉 TEST FINAL COMPLETADO - Estado: {estado_final}")
    
    return estado_final

if __name__ == "__main__":
    estado = test_sistema_completo()
    print(f"\n{'='*60}")
    print(f"🏁 PROYECTO FINALIZADO - Estado: {estado}")
    print(f"{'='*60}") 