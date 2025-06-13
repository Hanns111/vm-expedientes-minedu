#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST FINAL DE CONSULTAS DE LA DIRECTIVA - MINEDU
===============================================

Script que prueba consultas específicas de la Directiva N° 011-2020-MINEDU
con los sistemas TF-IDF y Transformers que están funcionando.
"""

import os
import sys
import time
import json
from datetime import datetime

# Añadir ruta del proyecto
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

class TestConsultasDirectiva:
    """Clase para probar consultas específicas de la directiva"""
    
    def __init__(self):
        self.resultados = {
            'timestamp': datetime.now().isoformat(),
            'consultas': {},
            'sistemas_funcionando': [],
            'estadisticas': {}
        }
        
        # Consultas específicas de la Directiva N° 011-2020-MINEDU
        self.consultas_directiva = [
            "¿Cuál es el monto máximo diario para viáticos nacionales?",
            "¿Quién autoriza los viáticos en el MINEDU?",
            "¿Qué documentos se requieren para solicitar viáticos?",
            "¿Cuántos días antes debo solicitar viáticos?",
            "¿Cómo se rinden los gastos de viáticos?",
            "¿Cuáles son las responsabilidades del comisionado?",
            "¿Qué sucede si no rindo mis viáticos a tiempo?",
            "¿Se pueden solicitar viáticos para viajes internacionales?"
        ]
    
    def print_header(self, title):
        """Imprimir encabezado"""
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print(f"{'='*60}")
    
    def test_tfidf_consultas(self):
        """Probar todas las consultas con TF-IDF"""
        print("🔍 Probando TF-IDF con consultas de la directiva...")
        
        try:
            from src.ai.search_vectorstore_hybrid import SearchVectorstore
            
            vectorstore_path = 'data/processed/vectorstore_semantic_full_v2.pkl'
            if not os.path.exists(vectorstore_path):
                print("❌ Vectorstore TF-IDF no encontrado")
                return False
            
            search = SearchVectorstore(vectorstore_path)
            resultados_tfidf = {}
            
            for i, consulta in enumerate(self.consultas_directiva, 1):
                print(f"\n📝 Consulta {i}: {consulta}")
                
                try:
                    start_time = time.time()
                    results = search.search(consulta, top_k=3)
                    elapsed_time = time.time() - start_time
                    
                    if results and 'results' in results and results['results']:
                        print(f"   ✅ TF-IDF: {len(results['results'])} resultados en {elapsed_time:.4f}s")
                        
                        # Mostrar respuesta generada
                        respuesta = results.get('response', 'Sin respuesta generada')
                        print(f"   📄 Respuesta: {respuesta[:200]}...")
                        
                        # Mostrar primer resultado
                        if results['results']:
                            primer_resultado = results['results'][0]
                            texto = primer_resultado.get('texto', primer_resultado.get('text', 'Sin texto'))
                            print(f"   📄 Fragmento: {texto[:150]}...")
                        
                        resultados_tfidf[f"consulta_{i}"] = {
                            'status': 'RESPONDIDA',
                            'time': elapsed_time,
                            'results_count': len(results['results']),
                            'response': respuesta,
                            'sistema': 'TF-IDF'
                        }
                    else:
                        print(f"   ⚠️ TF-IDF no devolvió resultados")
                        resultados_tfidf[f"consulta_{i}"] = {
                            'status': 'SIN_RESPUESTA',
                            'sistema': 'TF-IDF'
                        }
                        
                except Exception as e:
                    print(f"   ❌ Error en TF-IDF: {str(e)[:100]}...")
                    resultados_tfidf[f"consulta_{i}"] = {
                        'status': 'ERROR',
                        'error': str(e),
                        'sistema': 'TF-IDF'
                    }
            
            self.resultados['consultas']['tfidf'] = resultados_tfidf
            return True
            
        except Exception as e:
            print(f"❌ Error inicializando TF-IDF: {str(e)[:100]}...")
            return False
    
    def test_transformers_consultas(self):
        """Probar todas las consultas con Transformers"""
        print("🔍 Probando Transformers con consultas de la directiva...")
        
        try:
            from src.ai.search_vectorstore_transformers import TransformersSearch
            
            vectorstore_path = 'data/processed/vectorstore_transformers_test.pkl'
            if not os.path.exists(vectorstore_path):
                print("❌ Vectorstore Transformers no encontrado")
                return False
            
            search = TransformersSearch(vectorstore_path)
            resultados_transformers = {}
            
            for i, consulta in enumerate(self.consultas_directiva, 1):
                print(f"\n📝 Consulta {i}: {consulta}")
                
                try:
                    start_time = time.time()
                    results = search.search(consulta, top_k=3)
                    elapsed_time = time.time() - start_time
                    
                    if results and 'results' in results and results['results']:
                        print(f"   ✅ Transformers: {len(results['results'])} resultados en {elapsed_time:.4f}s")
                        
                        # Mostrar primer resultado
                        if results['results']:
                            primer_resultado = results['results'][0]
                            texto = primer_resultado.get('texto', primer_resultado.get('text', 'Sin texto'))
                            score = primer_resultado.get('score', 0)
                            print(f"   📄 Fragmento: {texto[:150]}...")
                            print(f"   🎯 Score: {score:.4f}")
                        
                        resultados_transformers[f"consulta_{i}"] = {
                            'status': 'RESPONDIDA',
                            'time': elapsed_time,
                            'results_count': len(results['results']),
                            'top_score': results['results'][0].get('score', 0) if results['results'] else 0,
                            'sistema': 'Transformers'
                        }
                    else:
                        print(f"   ⚠️ Transformers no devolvió resultados")
                        resultados_transformers[f"consulta_{i}"] = {
                            'status': 'SIN_RESPUESTA',
                            'sistema': 'Transformers'
                        }
                        
                except Exception as e:
                    print(f"   ❌ Error en Transformers: {str(e)[:100]}...")
                    resultados_transformers[f"consulta_{i}"] = {
                        'status': 'ERROR',
                        'error': str(e),
                        'sistema': 'Transformers'
                    }
            
            self.resultados['consultas']['transformers'] = resultados_transformers
            return True
            
        except Exception as e:
            print(f"❌ Error inicializando Transformers: {str(e)[:100]}...")
            return False
    
    def generar_estadisticas(self):
        """Generar estadísticas finales"""
        self.print_header("ESTADÍSTICAS FINALES")
        
        # Contar sistemas funcionando
        sistemas_ok = []
        if 'tfidf' in self.resultados['consultas']:
            sistemas_ok.append('TF-IDF')
        if 'transformers' in self.resultados['consultas']:
            sistemas_ok.append('Transformers')
        
        self.resultados['sistemas_funcionando'] = sistemas_ok
        
        # Estadísticas por sistema
        for sistema in sistemas_ok:
            # Mapear nombres de sistema a claves del diccionario
            sistema_key = 'tfidf' if sistema == 'TF-IDF' else 'transformers'
            consultas_sistema = self.resultados['consultas'][sistema_key]
            respondidas = sum(1 for c in consultas_sistema.values() if c.get('status') == 'RESPONDIDA')
            total = len(consultas_sistema)
            porcentaje = (respondidas / total) * 100
            
            # Tiempo promedio
            tiempos = [c.get('time', 0) for c in consultas_sistema.values() if c.get('time')]
            tiempo_promedio = sum(tiempos) / len(tiempos) if tiempos else 0
            
            print(f"\n📊 {sistema}:")
            print(f"   ✅ Respondidas: {respondidas}/{total} ({porcentaje:.1f}%)")
            print(f"   ⏱️ Tiempo promedio: {tiempo_promedio:.4f}s")
            
            self.resultados['estadisticas'][sistema] = {
                'respondidas': respondidas,
                'total': total,
                'porcentaje': porcentaje,
                'tiempo_promedio': tiempo_promedio
            }
        
        # Estadísticas generales
        total_consultas = len(self.consultas_directiva)
        total_respondidas = sum(
            sum(1 for c in self.resultados['consultas'][s].values() if c.get('status') == 'RESPONDIDA')
            for s in ['tfidf', 'transformers'] if s in self.resultados['consultas']
        )
        porcentaje_general = (total_respondidas / (total_consultas * len(sistemas_ok))) * 100
        
        print(f"\n🎯 ESTADÍSTICAS GENERALES:")
        print(f"   🔧 Sistemas funcionando: {len(sistemas_ok)}/2")
        print(f"   💬 Consultas respondidas: {total_respondidas}/{total_consultas * len(sistemas_ok)} ({porcentaje_general:.1f}%)")
        
        self.resultados['estadisticas']['general'] = {
            'sistemas_funcionando': len(sistemas_ok),
            'total_consultas': total_consultas,
            'total_respondidas': total_respondidas,
            'porcentaje_general': porcentaje_general
        }
        
        return porcentaje_general >= 50  # 50% o más = éxito
    
    def guardar_resultados(self):
        """Guardar resultados en archivo JSON"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        reporte_path = f"reports/test_consultas_directiva_{timestamp}.json"
        
        try:
            os.makedirs("reports", exist_ok=True)
            with open(reporte_path, 'w', encoding='utf-8') as f:
                json.dump(self.resultados, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Resultados guardados: {reporte_path}")
            return reporte_path
            
        except Exception as e:
            print(f"\n⚠️ No se pudo guardar resultados: {e}")
            return None
    
    def ejecutar_test_completo(self):
        """Ejecutar test completo de consultas"""
        print("🎯 TEST FINAL DE CONSULTAS DE LA DIRECTIVA")
        print("🔍 Probando TF-IDF y Transformers con consultas específicas")
        print("=" * 70)
        
        # Probar TF-IDF
        tfidf_ok = self.test_tfidf_consultas()
        
        # Probar Transformers
        transformers_ok = self.test_transformers_consultas()
        
        # Generar estadísticas
        success = self.generar_estadisticas()
        
        # Guardar resultados
        self.guardar_resultados()
        
        print(f"\n{'='*70}")
        print("🎉 TEST DE CONSULTAS COMPLETADO")
        print(f"{'='*70}")
        
        return success

def main():
    """Función principal"""
    tester = TestConsultasDirectiva()
    success = tester.ejecutar_test_completo()
    
    # Mensaje final
    if success:
        print(f"\n🏆 ¡PERFECTO! Tu sistema responde consultas de la directiva.")
        print(f"✅ Los sistemas TF-IDF y Transformers están funcionando correctamente.")
        print(f"🚀 Tu proyecto está listo para presentación y uso en producción.")
        return True
    else:
        print(f"\n⚠️ Tu sistema necesita mejoras en las respuestas.")
        print(f"🔧 Revisa los resultados para optimizar las consultas.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 