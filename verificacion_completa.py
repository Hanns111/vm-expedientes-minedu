#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRIPT DE VERIFICACIÓN COMPLETA - PROYECTO SISTEMA HÍBRIDO MINEDU
=================================================================

Este script verifica que TODOS los componentes del proyecto estén funcionando correctamente.
Ejecuta pruebas exhaustivas de cada sistema y genera un reporte completo.

EJECUTAR: python verificacion_completa.py
"""

import os
import sys
import json
import time
import pickle
from pathlib import Path
from datetime import datetime

# Añadir ruta del proyecto
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

class ProyectoVerificador:
    """Verificador completo del proyecto Sistema Híbrido MINEDU"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'systems': {},
            'files': {},
            'overall_status': 'UNKNOWN'
        }
        self.passed_tests = 0
        self.total_tests = 0
    
    def print_header(self, title):
        """Imprimir encabezado de sección"""
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print(f"{'='*60}")
    
    def test_result(self, test_name, success, details=""):
        """Registrar resultado de test"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        print(f"{status} - {test_name}")
        if details:
            print(f"    📋 {details}")
        
        self.results['tests'][test_name] = {
            'status': 'PASS' if success else 'FAIL',
            'details': details
        }
        
        return success
    
    def verificar_estructura_archivos(self):
        """Verificar que todos los archivos clave existen"""
        self.print_header("VERIFICACIÓN DE ESTRUCTURA DE ARCHIVOS")
        
        archivos_criticos = {
            # Código principal
            'src/ai/search_vectorstore_hybrid.py': 'Sistema TF-IDF',
            'src/ai/search_vectorstore_transformers.py': 'Sistema Transformers',
            'src/ai/search_vectorstore_bm25_fixed.py': 'Sistema BM25 corregido',
            'hybrid_system_implementation.py': 'Sistema Híbrido principal',
            
            # Datos
            'data/processed/chunks.json': 'Chunks de documentos',
            'data/processed/vectorstore_semantic_full_v2.pkl': 'Vectorstore TF-IDF',
            
            # Documentación
            'paper_cientifico/paper_final/paper_sistema_hibrido.md': 'Paper científico',
            'presentacion_final/presentacion_sistema_hibrido.md': 'Presentación ejecutiva',
            'CONTROL_PROYECTO.md': 'Control del proyecto',
            'README.md': 'Documentación principal',
            
            # Configuración
            'requirements.txt': 'Dependencias del proyecto'
        }
        
        archivos_encontrados = 0
        
        for archivo, descripcion in archivos_criticos.items():
            exists = os.path.exists(archivo)
            if exists:
                size = os.path.getsize(archivo)
                details = f"{descripcion} - {size} bytes"
            else:
                details = f"{descripcion} - NO ENCONTRADO"
            
            if self.test_result(f"Archivo: {archivo}", exists, details):
                archivos_encontrados += 1
        
        # Test resumen de archivos
        coverage = (archivos_encontrados / len(archivos_criticos)) * 100
        self.test_result(
            "Cobertura de archivos críticos", 
            coverage >= 80, 
            f"{archivos_encontrados}/{len(archivos_criticos)} archivos ({coverage:.1f}%)"
        )
    
    def verificar_sistema_tfidf(self):
        """Verificar sistema TF-IDF"""
        self.print_header("VERIFICACIÓN SISTEMA TF-IDF")
        
        try:
            from src.ai.search_vectorstore_hybrid import search_query
            self.test_result("Importación TF-IDF", True, "Módulo importado correctamente")
            
            # Prueba de búsqueda
            query = "¿Cuál es el monto máximo para viáticos?"
            start_time = time.time()
            results = search_query(query)
            elapsed_time = time.time() - start_time
            
            # Verificar resultados
            has_results = results and len(results) > 0
            self.test_result("Búsqueda TF-IDF", has_results, f"{len(results) if results else 0} resultados en {elapsed_time:.4f}s")
            
            if has_results:
                # Verificar estructura de resultados
                first_result = results[0]
                has_structure = isinstance(first_result, dict) and ('texto' in first_result or 'text' in first_result)
                self.test_result("Estructura resultados TF-IDF", has_structure, f"Claves: {list(first_result.keys()) if isinstance(first_result, dict) else 'N/A'}")
                
                # Verificar velocidad
                fast_enough = elapsed_time < 1.0
                self.test_result("Velocidad TF-IDF", fast_enough, f"{elapsed_time:.4f}s {'(rápido)' if fast_enough else '(lento)'}")
                
                self.results['systems']['tfidf'] = {
                    'status': 'FUNCTIONAL',
                    'response_time': elapsed_time,
                    'result_count': len(results)
                }
            else:
                self.results['systems']['tfidf'] = {'status': 'ERROR', 'error': 'No results'}
                
        except Exception as e:
            self.test_result("Sistema TF-IDF", False, f"Error: {str(e)}")
            self.results['systems']['tfidf'] = {'status': 'ERROR', 'error': str(e)}
    
    def verificar_sistema_transformers(self):
        """Verificar sistema Sentence Transformers"""
        self.print_header("VERIFICACIÓN SISTEMA SENTENCE TRANSFORMERS")
        
        try:
            from src.ai.search_vectorstore_transformers import search_semantic
            self.test_result("Importación Transformers", True, "Módulo importado correctamente")
            
            # Prueba de búsqueda
            query = "¿Cuál es el monto máximo para viáticos?"
            start_time = time.time()
            results = search_semantic(query)
            elapsed_time = time.time() - start_time
            
            # Verificar resultados
            has_results = results and len(results) > 0
            self.test_result("Búsqueda Transformers", has_results, f"{len(results) if results else 0} resultados en {elapsed_time:.4f}s")
            
            if has_results:
                # Verificar estructura
                first_result = results[0]
                has_structure = isinstance(first_result, dict)
                self.test_result("Estructura resultados Transformers", has_structure, f"Tipo: {type(first_result)}")
                
                # Verificar velocidad (más tolerante para Transformers)
                reasonable_speed = elapsed_time < 15.0
                self.test_result("Velocidad Transformers", reasonable_speed, f"{elapsed_time:.4f}s")
                
                self.results['systems']['transformers'] = {
                    'status': 'FUNCTIONAL',
                    'response_time': elapsed_time,
                    'result_count': len(results)
                }
            else:
                self.results['systems']['transformers'] = {'status': 'ERROR', 'error': 'No results'}
                
        except Exception as e:
            self.test_result("Sistema Transformers", False, f"Error: {str(e)}")
            self.results['systems']['transformers'] = {'status': 'ERROR', 'error': str(e)}
    
    def verificar_sistema_bm25(self):
        """Verificar sistema BM25"""
        self.print_header("VERIFICACIÓN SISTEMA BM25")
        
        try:
            from src.ai.search_vectorstore_bm25_fixed import BM25SearchFixed
            self.test_result("Importación BM25", True, "Módulo importado correctamente")
            
            # Verificar vectorstore
            vectorstore_path = 'data/processed/vectorstore_bm25_test.pkl'
            has_vectorstore = os.path.exists(vectorstore_path)
            self.test_result("Vectorstore BM25", has_vectorstore, f"Archivo: {vectorstore_path}")
            
            if has_vectorstore:
                # Inicializar BM25
                search = BM25SearchFixed(vectorstore_path)
                
                # Prueba de búsqueda
                query = "¿Cuál es el monto máximo para viáticos?"
                start_time = time.time()
                results = search.search(query, top_k=3)
                elapsed_time = time.time() - start_time
                
                # Verificar resultados
                has_results = results and len(results) > 0
                self.test_result("Búsqueda BM25", has_results, f"{len(results) if results else 0} resultados en {elapsed_time:.4f}s")
                
                self.results['systems']['bm25'] = {
                    'status': 'FUNCTIONAL' if has_results else 'NO_RESULTS',
                    'response_time': elapsed_time,
                    'result_count': len(results) if results else 0
                }
            else:
                self.results['systems']['bm25'] = {'status': 'ERROR', 'error': 'Vectorstore not found'}
                
        except Exception as e:
            self.test_result("Sistema BM25", False, f"Error: {str(e)}")
            self.results['systems']['bm25'] = {'status': 'ERROR', 'error': str(e)}
    
    def verificar_sistema_hibrido(self):
        """Verificar sistema híbrido"""
        self.print_header("VERIFICACIÓN SISTEMA HÍBRIDO")
        
        try:
            # Verificar que existe el archivo
            hybrid_file = 'hybrid_system_implementation.py'
            has_file = os.path.exists(hybrid_file)
            self.test_result("Archivo sistema híbrido", has_file, f"Archivo: {hybrid_file}")
            
            if has_file:
                # Intentar ejecutar una prueba básica
                exec_result = os.system(f'python -c "import sys; sys.path.append(\\".\\"); exec(open(\\"{hybrid_file}\\").read().split(\\"if __name__\\")[0])"')
                syntax_ok = exec_result == 0
                self.test_result("Sintaxis sistema híbrido", syntax_ok, "Código válido sin errores de sintaxis")
                
                self.results['systems']['hybrid'] = {
                    'status': 'AVAILABLE' if syntax_ok else 'SYNTAX_ERROR',
                    'file_exists': has_file
                }
            else:
                self.results['systems']['hybrid'] = {'status': 'ERROR', 'error': 'File not found'}
                
        except Exception as e:
            self.test_result("Sistema híbrido", False, f"Error: {str(e)}")
            self.results['systems']['hybrid'] = {'status': 'ERROR', 'error': str(e)}
    
    def verificar_documentacion(self):
        """Verificar documentación del proyecto"""
        self.print_header("VERIFICACIÓN DE DOCUMENTACIÓN")
        
        # Paper científico
        paper_path = 'paper_cientifico/paper_final/paper_sistema_hibrido.md'
        if os.path.exists(paper_path):
            with open(paper_path, 'r', encoding='utf-8') as f:
                paper_content = f.read()
            
            paper_complete = len(paper_content) > 2000 and 'Sistema Híbrido' in paper_content
            self.test_result("Paper científico", paper_complete, f"{len(paper_content)} caracteres")
        else:
            self.test_result("Paper científico", False, "Archivo no encontrado")
        
        # Presentación
        pres_path = 'presentacion_final/presentacion_sistema_hibrido.md'  
        if os.path.exists(pres_path):
            with open(pres_path, 'r', encoding='utf-8') as f:
                pres_content = f.read()
            
            pres_complete = len(pres_content) > 1000 and 'Slide' in pres_content
            self.test_result("Presentación ejecutiva", pres_complete, f"{len(pres_content)} caracteres")
        else:
            self.test_result("Presentación ejecutiva", False, "Archivo no encontrado")
        
        # README
        readme_exists = os.path.exists('README.md')
        self.test_result("README.md", readme_exists, "Documentación principal")
        
        # Requirements
        req_exists = os.path.exists('requirements.txt')
        self.test_result("requirements.txt", req_exists, "Lista de dependencias")
    
    def verificar_datos(self):
        """Verificar integridad de datos"""
        self.print_header("VERIFICACIÓN DE DATOS")
        
        # Chunks de datos
        chunks_path = 'data/processed/chunks.json'
        if os.path.exists(chunks_path):
            try:
                with open(chunks_path, 'r', encoding='utf-8') as f:
                    chunks = json.load(f)
                
                chunks_valid = isinstance(chunks, list) and len(chunks) > 0
                self.test_result("Chunks de datos", chunks_valid, f"{len(chunks) if chunks_valid else 0} chunks cargados")
                
                if chunks_valid and len(chunks) > 0:
                    first_chunk = chunks[0]
                    has_structure = isinstance(first_chunk, dict) and ('texto' in first_chunk or 'text' in first_chunk)
                    self.test_result("Estructura de chunks", has_structure, f"Claves: {list(first_chunk.keys()) if isinstance(first_chunk, dict) else 'N/A'}")
                    
            except Exception as e:
                self.test_result("Chunks de datos", False, f"Error cargando: {str(e)}")
        else:
            self.test_result("Chunks de datos", False, "Archivo no encontrado")
        
        # Vectorstore TF-IDF
        vectorstore_path = 'data/processed/vectorstore_semantic_full_v2.pkl'
        if os.path.exists(vectorstore_path):
            try:
                with open(vectorstore_path, 'rb') as f:
                    vectorstore = pickle.load(f)
                
                vectorstore_valid = isinstance(vectorstore, dict)
                self.test_result("Vectorstore TF-IDF", vectorstore_valid, f"Claves: {list(vectorstore.keys()) if vectorstore_valid else 'N/A'}")
                
            except Exception as e:
                self.test_result("Vectorstore TF-IDF", False, f"Error cargando: {str(e)}")
        else:
            self.test_result("Vectorstore TF-IDF", False, "Archivo no encontrado")
    
    def generar_reporte_final(self):
        """Generar reporte final de verificación"""
        self.print_header("REPORTE FINAL DE VERIFICACIÓN")
        
        # Calcular porcentaje de éxito
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        # Determinar estado general
        if success_rate >= 90:
            overall_status = "EXCELENTE"
            status_emoji = "🏆"
        elif success_rate >= 75:
            overall_status = "BUENO"  
            status_emoji = "✅"
        elif success_rate >= 60:
            overall_status = "ACEPTABLE"
            status_emoji = "⚠️"
        else:
            overall_status = "REQUIERE ATENCIÓN"
            status_emoji = "❌"
        
        self.results['overall_status'] = overall_status
        self.results['success_rate'] = success_rate
        self.results['passed_tests'] = self.passed_tests
        self.results['total_tests'] = self.total_tests
        
        print(f"\n{status_emoji} ESTADO GENERAL: {overall_status}")
        print(f"📊 TESTS PASADOS: {self.passed_tests}/{self.total_tests} ({success_rate:.1f}%)")
        
        # Resumen por sistemas
        print(f"\n📋 RESUMEN DE SISTEMAS:")
        for system_name, system_data in self.results['systems'].items():
            status = system_data.get('status', 'UNKNOWN')
            if status == 'FUNCTIONAL':
                print(f"  ✅ {system_name.upper()}: Funcional")
            elif status == 'NO_RESULTS':
                print(f"  ⚠️ {system_name.upper()}: Sin resultados")
            else:
                print(f"  ❌ {system_name.upper()}: {status}")
        
        # Guardar reporte
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"verificacion_proyecto_{timestamp}.json"
        
        try:
            os.makedirs("reports", exist_ok=True)
            report_path = f"reports/{report_file}"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Reporte guardado: {report_path}")
            
        except Exception as e:
            print(f"\n⚠️ No se pudo guardar reporte: {e}")
        
        return overall_status, success_rate
    
    def ejecutar_verificacion_completa(self):
        """Ejecutar toda la verificación"""
        print("🎯 VERIFICACIÓN COMPLETA DEL PROYECTO SISTEMA HÍBRIDO MINEDU")
        print("🔍 Ejecutando tests exhaustivos de todos los componentes...")
        print("=" * 70)
        
        # Ejecutar todas las verificaciones
        self.verificar_estructura_archivos()
        self.verificar_datos()
        self.verificar_sistema_tfidf()
        self.verificar_sistema_transformers()
        self.verificar_sistema_bm25()
        self.verificar_sistema_hibrido()
        self.verificar_documentacion()
        
        # Generar reporte final
        status, rate = self.generar_reporte_final()
        
        print(f"\n{'='*70}")
        print("🎉 VERIFICACIÓN COMPLETADA")
        print(f"{'='*70}")
        
        return status, rate

def main():
    """Función principal"""
    verificador = ProyectoVerificador()
    status, rate = verificador.ejecutar_verificacion_completa()
    
    # Mensaje final
    if rate >= 90:
        print(f"\n🏆 ¡EXCELENTE! Tu proyecto está en condiciones óptimas.")
        print(f"🚀 Listo para presentar, publicar o implementar.")
    elif rate >= 75:
        print(f"\n✅ ¡BIEN! Tu proyecto está funcionando correctamente.")
        print(f"🔧 Algunos ajustes menores podrían mejorarlo.")
    else:
        print(f"\n⚠️ Tu proyecto necesita algunas correcciones.")
        print(f"🔍 Revisa el reporte para identificar problemas.")
    
    return rate >= 75

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 