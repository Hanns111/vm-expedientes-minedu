#!/usr/bin/env python3
"""
Pipeline Asíncrono con Timeouts y Métricas Avanzadas
===================================================

Pipeline optimizado que ejecuta componentes en paralelo donde es posible,
con timeouts configurables y métricas granulares por componente.
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Union
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from prometheus_client import Counter, Histogram, Gauge
import aiofiles

from .cache_system import get_cache, cached

# Métricas específicas del pipeline
PIPELINE_OPERATIONS_TOTAL = Counter('pipeline_operations_total', 'Total pipeline operations', ['operation', 'status'])
PIPELINE_DURATION = Histogram('pipeline_duration_seconds', 'Pipeline operation duration', ['operation'])
PIPELINE_TIMEOUTS_TOTAL = Counter('pipeline_timeouts_total', 'Total pipeline timeouts', ['operation'])
ACTIVE_PIPELINES = Gauge('active_pipelines', 'Number of active pipeline executions')

logger = logging.getLogger(__name__)

@dataclass
class PipelineMetrics:
    """Métricas detalladas de ejecución del pipeline"""
    total_time: float = 0.0
    extraction_time: float = 0.0
    validation_time: float = 0.0
    dialog_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    timeouts: int = 0
    parallel_speedup: float = 1.0
    
class AsyncTimeoutError(Exception):
    """Error específico para timeouts del pipeline"""
    pass

class OptimizedAsyncPipeline:
    """
    Pipeline asíncrono optimizado para procesamiento de documentos MINEDU.
    
    Características:
    - Paralelización inteligente de componentes independientes
    - Timeouts configurables por operación
    - Cache multi-nivel integrado
    - Métricas detalladas por componente
    - Manejo robusto de errores y fallbacks
    """
    
    def __init__(self, max_workers: int = 8, default_timeout: float = 30.0):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.cache = get_cache()
        self.default_timeout = default_timeout
        
        # Timeouts específicos por operación (en segundos)
        self.timeouts = {
            'extraction': 20.0,
            'entity_detection': 10.0,
            'validation': 15.0,
            'dialog_generation': 5.0,
            'total_pipeline': 45.0
        }
        
        logger.info(f"🚀 AsyncPipeline inicializado - Workers: {max_workers}, Timeout: {default_timeout}s")
    
    async def process_document_async(self, 
                                   pdf_path: str, 
                                   location: str = "regiones",
                                   enable_cache: bool = True) -> Dict[str, Any]:
        """
        Procesar documento de forma asíncrona con paralelización y métricas.
        
        Args:
            pdf_path: Ruta al documento PDF
            location: Ubicación para validación (lima/regiones)
            enable_cache: Habilitar cache (útil para testing)
            
        Returns:
            Resultado completo del pipeline con métricas
        """
        pipeline_start = time.time()
        metrics = PipelineMetrics()
        
        # Incrementar contador de pipelines activos
        ACTIVE_PIPELINES.inc()
        
        try:
            logger.info(f"📊 Iniciando pipeline asíncrono: {pdf_path}")
            
            # FASE 1: Componentes paralelos independientes
            parallel_start = time.time()
            
            # Ejecutar en paralelo: extracción, detección de entidades, carga de reglas
            tasks = {
                'extraction': self._extract_tables_async(pdf_path, enable_cache),
                'entities': self._extract_entities_async(pdf_path, enable_cache),
                'rules_engine': self._load_rules_engine_async(enable_cache)
            }
            
            # Esperar todos los componentes paralelos con timeout
            try:
                parallel_results = await asyncio.wait_for(
                    self._execute_parallel_tasks(tasks),
                    timeout=max(self.timeouts['extraction'], 
                              self.timeouts['entity_detection'])
                )
            except asyncio.TimeoutError:
                PIPELINE_TIMEOUTS_TOTAL.labels(operation='parallel_phase').inc()
                metrics.timeouts += 1
                raise AsyncTimeoutError("Timeout en fase paralela del pipeline")
            
            parallel_time = time.time() - parallel_start
            metrics.parallel_speedup = self._calculate_speedup(parallel_time, tasks)
            
            # FASE 2: Validación secuencial (depende de resultados anteriores)
            validation_start = time.time()
            
            try:
                validation_result = await asyncio.wait_for(
                    self._validate_concepts_async(
                        parallel_results['extraction'], 
                        parallel_results['entities'],
                        parallel_results['rules_engine'],
                        location,
                        enable_cache
                    ),
                    timeout=self.timeouts['validation']
                )
            except asyncio.TimeoutError:
                PIPELINE_TIMEOUTS_TOTAL.labels(operation='validation').inc()
                metrics.timeouts += 1
                raise AsyncTimeoutError("Timeout en validación normativa")
                
            metrics.validation_time = time.time() - validation_start
            
            # FASE 3: Generación de diálogo (si es necesario)
            dialog_result = None
            if not validation_result.get('valid', True):
                dialog_start = time.time()
                
                try:
                    dialog_result = await asyncio.wait_for(
                        self._generate_dialog_async(validation_result, enable_cache),
                        timeout=self.timeouts['dialog_generation']
                    )
                except asyncio.TimeoutError:
                    PIPELINE_TIMEOUTS_TOTAL.labels(operation='dialog').inc()
                    metrics.timeouts += 1
                    logger.warning("⚠️ Timeout en generación de diálogo, continuando sin él")
                    
                metrics.dialog_time = time.time() - dialog_start
            
            # Compilar resultado final
            metrics.total_time = time.time() - pipeline_start
            cache_stats = self.cache.get_stats()
            
            result = {
                'success': True,
                'extraction_result': parallel_results['extraction'],
                'entities_result': parallel_results['entities'], 
                'validation_result': validation_result,
                'dialog_result': dialog_result,
                'metrics': {
                    'total_time': round(metrics.total_time, 3),
                    'extraction_time': round(parallel_results.get('extraction_time', 0), 3),
                    'validation_time': round(metrics.validation_time, 3),
                    'dialog_time': round(metrics.dialog_time, 3),
                    'parallel_speedup': round(metrics.parallel_speedup, 2),
                    'cache_hit_rate': cache_stats['l1_hit_rate'],
                    'timeouts': metrics.timeouts
                },
                'cache_info': cache_stats
            }
            
            # Métricas Prometheus
            PIPELINE_OPERATIONS_TOTAL.labels(operation='complete', status='success').inc()
            PIPELINE_DURATION.labels(operation='complete').observe(metrics.total_time)
            
            logger.info(f"✅ Pipeline completado en {metrics.total_time:.3f}s "
                       f"(speedup: {metrics.parallel_speedup:.2f}x)")
            
            return result
            
        except Exception as e:
            metrics.total_time = time.time() - pipeline_start
            
            PIPELINE_OPERATIONS_TOTAL.labels(operation='complete', status='error').inc()
            PIPELINE_DURATION.labels(operation='error').observe(metrics.total_time)
            
            logger.error(f"❌ Error en pipeline: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'metrics': {
                    'total_time': round(metrics.total_time, 3),
                    'timeouts': metrics.timeouts
                }
            }
            
        finally:
            # Decrementar contador de pipelines activos
            ACTIVE_PIPELINES.dec()
    
    async def _execute_parallel_tasks(self, tasks: Dict[str, asyncio.Task]) -> Dict[str, Any]:
        """Ejecutar tareas en paralelo y recopilar resultados"""
        results = {}
        
        # Ejecutar todas las tareas
        completed_tasks = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # Mapear resultados con nombres de tareas
        for i, (task_name, task) in enumerate(tasks.items()):
            result = completed_tasks[i]
            
            if isinstance(result, Exception):
                logger.error(f"❌ Error en tarea {task_name}: {result}")
                results[task_name] = None
            else:
                results[task_name] = result
                
        return results
    
    @cached('hybrid', ttl=1800)  # Cache por 30 minutos
    async def _extract_tables_async(self, pdf_path: str, enable_cache: bool = True) -> Dict[str, Any]:
        """Extraer tablas de forma asíncrona con cache"""
        start_time = time.time()
        
        # Simular extracción de tablas (reemplazar con implementación real)
        await asyncio.sleep(0.1)  # Simular trabajo de extracción
        
        extraction_time = time.time() - start_time
        
        # Mock result - reemplazar con extractor real
        result = {
            'tables': [
                {'numeral': '8.4.17.1', 'amount': 35.0, 'concepto': 'Traslado aeropuerto'},
                {'numeral': '8.4.17.2', 'amount': 25.0, 'concepto': 'Traslado terrapuerto'}
            ],
            'confidence': 0.94,
            'extraction_time': extraction_time
        }
        
        PIPELINE_OPERATIONS_TOTAL.labels(operation='extraction', status='success').inc()
        PIPELINE_DURATION.labels(operation='extraction').observe(extraction_time)
        
        return result
    
    @cached('adaptive', ttl=3600)  # Cache por 1 hora
    async def _extract_entities_async(self, pdf_path: str, enable_cache: bool = True) -> Dict[str, Any]:
        """Extraer entidades de forma asíncrona"""
        start_time = time.time()
        
        # Simular detección de entidades
        await asyncio.sleep(0.05)
        
        extraction_time = time.time() - start_time
        
        result = {
            'amounts': ['35.00', '25.00'],
            'numerals': ['8.4.17.1', '8.4.17.2'],
            'extraction_time': extraction_time
        }
        
        PIPELINE_OPERATIONS_TOTAL.labels(operation='entities', status='success').inc()
        PIPELINE_DURATION.labels(operation='entities').observe(extraction_time)
        
        return result
    
    @cached('declarative', ttl=7200)  # Cache por 2 horas
    async def _load_rules_engine_async(self, enable_cache: bool = True) -> Dict[str, Any]:
        """Cargar motor de reglas de forma asíncrona"""
        start_time = time.time()
        
        # Simular carga de reglas
        await asyncio.sleep(0.02)
        
        load_time = time.time() - start_time
        
        result = {
            'rules_loaded': True,
            'catalog_version': '2.0',
            'load_time': load_time
        }
        
        PIPELINE_OPERATIONS_TOTAL.labels(operation='rules_loading', status='success').inc()
        PIPELINE_DURATION.labels(operation='rules_loading').observe(load_time)
        
        return result
    
    async def _validate_concepts_async(self, 
                                     extraction_result: Dict[str, Any],
                                     entities_result: Dict[str, Any], 
                                     rules_engine: Dict[str, Any],
                                     location: str,
                                     enable_cache: bool = True) -> Dict[str, Any]:
        """Validar conceptos usando motor de reglas"""
        start_time = time.time()
        
        # Simular validación normativa
        await asyncio.sleep(0.08)
        
        # Mock validation - reemplazar con validador real
        total_amount = sum(table.get('amount', 0) for table in extraction_result.get('tables', []))
        daily_limit = 45.0 if location == 'lima' else 30.0
        
        validation_time = time.time() - start_time
        
        result = {
            'valid': total_amount <= daily_limit,
            'total_amount': total_amount,
            'daily_limit': daily_limit,
            'location': location,
            'violations': [] if total_amount <= daily_limit else [f"Total S/{total_amount} excede límite diario S/{daily_limit}"],
            'suggestions': [] if total_amount <= daily_limit else ["Distribuir servicios en varios días"],
            'validation_time': validation_time
        }
        
        PIPELINE_OPERATIONS_TOTAL.labels(operation='validation', status='success').inc()
        PIPELINE_DURATION.labels(operation='validation').observe(validation_time)
        
        return result
    
    async def _generate_dialog_async(self, validation_result: Dict[str, Any], enable_cache: bool = True) -> Dict[str, Any]:
        """Generar diálogo interactivo de forma asíncrona"""
        start_time = time.time()
        
        # Simular generación de diálogo
        await asyncio.sleep(0.03)
        
        dialog_time = time.time() - start_time
        
        result = {
            'dialog_required': True,
            'dialog_type': 'daily_limit_exceeded',
            'message': f"El total excede el límite diario. ¿Cómo desea proceder?",
            'options': [
                {'id': 'distribute_days', 'text': 'Distribuir en varios días'},
                {'id': 'reduce_amounts', 'text': 'Reducir montos'}
            ],
            'dialog_time': dialog_time
        }
        
        PIPELINE_OPERATIONS_TOTAL.labels(operation='dialog', status='success').inc()
        PIPELINE_DURATION.labels(operation='dialog').observe(dialog_time)
        
        return result
    
    def _calculate_speedup(self, parallel_time: float, tasks: Dict[str, asyncio.Task]) -> float:
        """Calcular speedup teórico vs ejecución secuencial"""
        # Estimar tiempo secuencial basado en operaciones típicas
        sequential_time = 0.1 + 0.05 + 0.02  # extraction + entities + rules
        
        if parallel_time > 0:
            return sequential_time / parallel_time
        return 1.0
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar salud del pipeline"""
        start_time = time.time()
        
        try:
            # Test básico de componentes
            test_tasks = {
                'cache': self._test_cache(),
                'async_execution': self._test_async_execution()
            }
            
            results = await asyncio.wait_for(
                asyncio.gather(*test_tasks.values(), return_exceptions=True),
                timeout=5.0
            )
            
            health_time = time.time() - start_time
            
            return {
                'healthy': all(not isinstance(r, Exception) for r in results),
                'cache_available': self.cache.redis_available,
                'active_pipelines': ACTIVE_PIPELINES._value.get(),
                'health_check_time': round(health_time, 3),
                'components': {
                    'cache': not isinstance(results[0], Exception),
                    'async_execution': not isinstance(results[1], Exception)
                }
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'health_check_time': round(time.time() - start_time, 3)
            }
    
    async def _test_cache(self):
        """Test básico del sistema de cache"""
        test_key = "health_check_test"
        self.cache.set('test', test_key, {'test': True}, ttl=10)
        result = self.cache.get('test', test_key)
        return result is not None
    
    async def _test_async_execution(self):
        """Test básico de ejecución asíncrona"""
        await asyncio.sleep(0.001)
        return True