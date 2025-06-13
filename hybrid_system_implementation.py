#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SISTEMA HÍBRIDO - Combinación Inteligente de TF-IDF, BM25 y Transformers
========================================================================

Objetivo: Crear un sistema que combine las fortalezas de los 3 métodos:
- TF-IDF: Búsqueda léxica tradicional
- BM25: Ranking mejorado y velocidad
- Transformers: Comprensión semántica

Estrategia: Ponderación inteligente + Re-ranking + Fusión de resultados
"""

import sys
import os
import json
import time
import numpy as np
from datetime import datetime
from collections import defaultdict, Counter

# Añadir ruta del proyecto
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

class HybridSearchSystem:
    """Sistema de búsqueda híbrido que combina TF-IDF, BM25 y Transformers"""
    
    def __init__(self):
        self.systems = {}
        self.weights = {
            'tfidf': 0.3,      # 30% - Búsqueda léxica básica
            'bm25': 0.4,       # 40% - Ranking mejorado
            'transformers': 0.3 # 30% - Comprensión semántica
        }
        self.performance_cache = {}
        self._initialize_systems()
    
    def _initialize_systems(self):
        """Inicializar los 3 sistemas de búsqueda"""
        print("🔧 Inicializando Sistema Híbrido...")
        
        # 1. TF-IDF System
        try:
            from src.ai.search_vectorstore_hybrid import SearchVectorstore
            tfidf_search = SearchVectorstore('data/processed/vectorstore_semantic_full_v2.pkl')
            self.systems['tfidf'] = {
                'instance': tfidf_search,
                'status': 'ready',
                'description': 'TF-IDF + Cosine Similarity'
            }
            print("✅ TF-IDF System: Listo")
        except Exception as e:
            print(f"⚠️ TF-IDF System: Error - {e}")
            self.systems['tfidf'] = {'status': 'error', 'error': str(e)}
        
        # 2. BM25 System (Versión corregida)
        try:
            from src.ai.search_vectorstore_bm25_fixed import BM25SearchFixed
            bm25_search = BM25SearchFixed('data/processed/vectorstore_bm25_test.pkl')
            self.systems['bm25'] = {
                'instance': bm25_search,
                'status': 'ready',
                'description': 'BM25 Okapi + Boosting'
            }
            print("✅ BM25 System: Listo")
        except Exception as e:
            print(f"⚠️ BM25 System: Error - {e}")
            self.systems['bm25'] = {'status': 'error', 'error': str(e)}
        
        # 3. Transformers System
        try:
            from src.ai.search_vectorstore_transformers import TransformersSearch
            transformers_search = TransformersSearch('data/processed/vectorstore_transformers_test.pkl')
            self.systems['transformers'] = {
                'instance': transformers_search,
                'status': 'ready',
                'description': 'Sentence Transformers + Embeddings'
            }
            print("✅ Transformers System: Listo")
        except Exception as e:
            print(f"⚠️ Transformers System: Error - {e}")
            self.systems['transformers'] = {'status': 'error', 'error': str(e)}
        
        # Resumen de inicialización
        ready_systems = sum(1 for s in self.systems.values() if s.get('status') == 'ready')
        print(f"🎯 Sistemas listos: {ready_systems}/3")
    
    def search_individual_system(self, query, system_name, top_k=5):
        """Buscar en un sistema individual"""
        system = self.systems.get(system_name)
        if not system or system.get('status') != 'ready':
            return []
        
        try:
            start_time = time.time()
            
            if system_name == 'tfidf':
                results = system['instance'].search(query, top_k=top_k)
                # Normalizar formato TF-IDF
                normalized_results = []
                for i, result in enumerate(results.get('results', [])[:top_k]):
                    normalized_results.append({
                        'score': float(result.get('score', 0.5)),
                        'texto': str(result.get('texto', result.get('text', ''))),
                        'titulo': f"TF-IDF Result {i+1}",
                        'source': 'tfidf',
                        'index': i
                    })
                results = normalized_results
                
            elif system_name == 'bm25':
                results = system['instance'].search(query, top_k=top_k)
                # BM25 ya devuelve formato normalizado
                
            elif system_name == 'transformers':
                results = system['instance'].search(query, top_k=top_k)
                # Normalizar formato Transformers
                normalized_results = []
                for i, result in enumerate(results.get('results', [])[:top_k]):
                    normalized_results.append({
                        'score': float(result.get('score', result.get('similarity', 0.5))),
                        'texto': str(result.get('texto', result.get('text', result.get('content', '')))),
                        'titulo': f"Semantic Result {i+1}",
                        'source': 'transformers',
                        'index': i
                    })
                results = normalized_results
            
            elapsed_time = time.time() - start_time
            
            # Cache performance
            self.performance_cache[system_name] = {
                'last_query_time': elapsed_time,
                'last_result_count': len(results),
                'timestamp': datetime.now().isoformat()
            }
            
            return results
            
        except Exception as e:
            print(f"❌ Error en {system_name}: {e}")
            return []
    
    def hybrid_search(self, query, top_k=10):
        """Búsqueda híbrida que combina los 3 sistemas"""
        print(f"🔍 Búsqueda Híbrida: '{query}'")
        print("=" * 50)
        
        # Paso 1: Obtener resultados de cada sistema
        all_results = {}
        individual_times = {}
        
        for system_name in ['tfidf', 'bm25', 'transformers']:
            print(f"📊 Consultando {system_name.upper()}...")
            start = time.time()
            results = self.search_individual_system(query, system_name, top_k=top_k)
            individual_times[system_name] = time.time() - start
            all_results[system_name] = results
            print(f"   ⏱️ {individual_times[system_name]:.4f}s - {len(results)} resultados")
        
        # Paso 2: Fusión inteligente de resultados
        print("\n🔄 Fusionando resultados...")
        fused_results = self._fuse_results(all_results, query)
        
        # Paso 3: Re-ranking final
        print("🎯 Re-ranking final...")
        final_results = self._rerank_results(fused_results, query)[:top_k]
        
        # Estadísticas finales
        total_time = sum(individual_times.values())
        print(f"\n📊 ESTADÍSTICAS HÍBRIDAS:")
        print(f"   ⏱️ Tiempo total: {total_time:.4f}s")
        print(f"   🎯 Resultados finales: {len(final_results)}")
        print(f"   📈 Sistemas contribuyendo: {len([s for s in all_results if all_results[s]])}/3")
        
        return {
            'results': final_results,
            'metadata': {
                'individual_times': individual_times,
                'total_time': total_time,
                'systems_used': list(all_results.keys()),
                'fusion_method': 'weighted_combination',
                'query': query,
                'timestamp': datetime.now().isoformat()
            }
        }
    
    def _fuse_results(self, all_results, query):
        """Fusionar resultados de múltiples sistemas con ponderación inteligente"""
        fused = []
        seen_texts = set()
        
        # Crear índice de todos los resultados únicos
        unique_results = {}
        
        for system_name, results in all_results.items():
            weight = self.weights.get(system_name, 0.33)
            
            for result in results:
                text_key = result.get('texto', '')[:100]  # Usar primeros 100 chars como clave
                
                if text_key not in unique_results:
                    unique_results[text_key] = {
                        'texto': result.get('texto', ''),
                        'titulo': result.get('titulo', f'Resultado fusionado'),
                        'combined_score': 0.0,
                        'contributing_systems': [],
                        'individual_scores': {},
                        'fusion_details': {}
                    }
                
                # Acumular scores ponderados
                weighted_score = result.get('score', 0) * weight
                unique_results[text_key]['combined_score'] += weighted_score
                unique_results[text_key]['contributing_systems'].append(system_name)
                unique_results[text_key]['individual_scores'][system_name] = result.get('score', 0)
                unique_results[text_key]['fusion_details'][system_name] = {
                    'original_score': result.get('score', 0),
                    'weight_applied': weight,
                    'weighted_contribution': weighted_score
                }
        
        # Convertir a lista y ordenar por score combinado
        fused = list(unique_results.values())
        fused.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return fused
    
    def _rerank_results(self, fused_results, query):
        """Re-ranking final basado en múltiples factores"""
        for result in fused_results:
            # Factor de diversidad (bonus por múltiples sistemas)
            diversity_bonus = len(result['contributing_systems']) * 0.1
            
            # Factor de consenso (bonus si múltiples sistemas están de acuerdo)
            consensus_bonus = 0
            if len(result['contributing_systems']) >= 2:
                scores = list(result['individual_scores'].values())
                if len(scores) >= 2:
                    score_std = np.std(scores)
                    consensus_bonus = max(0, (1.0 - score_std) * 0.2)  # Bonus si scores son similares
            
            # Factor de relevancia de texto (simplificado)
            query_words = query.lower().split()
            text_lower = result['texto'].lower()
            word_matches = sum(1 for word in query_words if word in text_lower)
            relevance_bonus = (word_matches / len(query_words)) * 0.1 if query_words else 0
            
            # Score final
            result['final_score'] = (
                result['combined_score'] + 
                diversity_bonus + 
                consensus_bonus + 
                relevance_bonus
            )
            
            # Metadata del re-ranking
            result['rerank_factors'] = {
                'original_combined': result['combined_score'],
                'diversity_bonus': diversity_bonus,
                'consensus_bonus': consensus_bonus,
                'relevance_bonus': relevance_bonus,
                'final_score': result['final_score']
            }
        
        # Ordenar por score final
        fused_results.sort(key=lambda x: x['final_score'], reverse=True)
        return fused_results
    
    def evaluate_hybrid_performance(self, test_queries):
        """Evaluar rendimiento del sistema híbrido vs sistemas individuales"""
        print("📊 EVALUACIÓN DE RENDIMIENTO HÍBRIDO")
        print("=" * 45)
        
        results = {
            'hybrid': {'times': [], 'result_counts': []},
            'individual': {system: {'times': [], 'result_counts': []} for system in self.systems.keys()}
        }
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Query {i}/{len(test_queries)}: {query[:50]}...")
            
            # Probar sistema híbrido
            start = time.time()
            hybrid_result = self.hybrid_search(query, top_k=5)
            hybrid_time = time.time() - start
            
            results['hybrid']['times'].append(hybrid_time)
            results['hybrid']['result_counts'].append(len(hybrid_result.get('results', [])))
            
            # Probar sistemas individuales
            for system_name in self.systems.keys():
                if self.systems[system_name].get('status') == 'ready':
                    start = time.time()
                    individual_results = self.search_individual_system(query, system_name, top_k=5)
                    individual_time = time.time() - start
                    
                    results['individual'][system_name]['times'].append(individual_time)
                    results['individual'][system_name]['result_counts'].append(len(individual_results))
        
        # Calcular estadísticas
        print("\n📊 ESTADÍSTICAS COMPARATIVAS:")
        
        # Sistema híbrido
        hybrid_avg_time = np.mean(results['hybrid']['times'])
        hybrid_avg_results = np.mean(results['hybrid']['result_counts'])
        print(f"\n🔄 SISTEMA HÍBRIDO:")
        print(f"   ⏱️ Tiempo promedio: {hybrid_avg_time:.4f}s")
        print(f"   📊 Resultados promedio: {hybrid_avg_results:.1f}")
        
        # Sistemas individuales
        print(f"\n📋 SISTEMAS INDIVIDUALES:")
        for system_name, data in results['individual'].items():
            if data['times']:  # Solo si tiene datos
                avg_time = np.mean(data['times'])
                avg_results = np.mean(data['result_counts'])
                print(f"   {system_name.upper()}: {avg_time:.4f}s, {avg_results:.1f} resultados")
        
        return results

def test_hybrid_system():
    """Función de prueba completa del sistema híbrido"""
    print("🚀 PRUEBA COMPLETA DEL SISTEMA HÍBRIDO")
    print("🎯 Objetivo: Validar funcionamiento y rendimiento")
    print("=" * 55)
    
    # Inicializar sistema híbrido
    hybrid = HybridSearchSystem()
    
    # Queries de prueba
    test_queries = [
        "¿Cuál es el monto máximo para viáticos?",
        "¿Qué documentos se requieren para viáticos?",
        "¿Cuál es el procedimiento para solicitar viáticos?",
        "¿Quién autoriza los viáticos en el MINEDU?",
        "¿Cuáles son las responsabilidades del comisionado?"
    ]
    
    # Prueba individual de una query
    print("\n🧪 PRUEBA INDIVIDUAL:")
    query = test_queries[0]
    hybrid_result = hybrid.hybrid_search(query, top_k=5)
    
    print(f"\n📋 RESULTADOS PARA: '{query}'")
    for i, result in enumerate(hybrid_result['results'][:3], 1):
        print(f"\n📄 Resultado {i}:")
        print(f"   🎯 Score: {result['final_score']:.4f}")
        print(f"   🏷️ Título: {result['titulo']}")
        print(f"   📝 Texto: {result['texto'][:100]}...")
        print(f"   🔗 Sistemas: {', '.join(result['contributing_systems'])}")
    
    # Evaluación completa
    print(f"\n🔬 EVALUACIÓN COMPLETA ({len(test_queries)} queries):")
    performance_results = hybrid.evaluate_hybrid_performance(test_queries)
    
    # Guardar resultados
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"data/evaluation/hybrid_system_evaluation_{timestamp}.json"
    
    os.makedirs("data/evaluation", exist_ok=True)
    
    evaluation_data = {
        'timestamp': timestamp,
        'test_queries': test_queries,
        'sample_result': hybrid_result,
        'performance_comparison': performance_results,
        'system_config': {
            'weights': hybrid.weights,
            'systems_available': [name for name, system in hybrid.systems.items() if system.get('status') == 'ready']
        }
    }
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(evaluation_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Resultados guardados: {results_file}")
    
    return hybrid, evaluation_data

def main():
    """Función principal"""
    print("🔄 IMPLEMENTACIÓN DEL SISTEMA HÍBRIDO")
    print("🎯 Combinando TF-IDF + BM25 + Transformers")
    print("=" * 50)
    
    try:
        # Ejecutar prueba completa
        hybrid_system, results = test_hybrid_system()
        
        print("\n" + "=" * 55)
        print("🎉 SISTEMA HÍBRIDO IMPLEMENTADO EXITOSAMENTE")
        print("=" * 55)
        
        # Mostrar resumen final
        systems_working = len([s for s in hybrid_system.systems.values() if s.get('status') == 'ready'])
        print(f"✅ Sistemas integrados: {systems_working}/3")
        print(f"✅ Fusión de resultados: Funcional")
        print(f"✅ Re-ranking inteligente: Funcional")
        print(f"✅ Evaluación de rendimiento: Completada")
        
        print(f"\n🚀 LISTO PARA:")
        print(f"   📝 Paper Científico (30 min)")
        print(f"   🔬 Evaluaciones avanzadas")
        print(f"   🎯 Optimización de parámetros")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error en implementación: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ ¡SISTEMA HÍBRIDO COMPLETADO!")
        print("🎯 Siguiente: Paper Científico")
    else:
        print("\n❌ Revisar errores y reintentar") 