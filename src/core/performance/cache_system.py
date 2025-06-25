#!/usr/bin/env python3
"""
Sistema de Cache Multi-Nivel con Métricas Prometheus
===================================================

Implementa cache L1 (memoria) + L2 (Redis) con instrumentación completa
y namespacing por componente del sistema.
"""

import redis
import pickle
import hashlib
import time
import logging
from typing import Any, Optional, Dict, Union
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge

# Métricas Prometheus para cache
CACHE_HITS_TOTAL = Counter('cache_hits_total', 'Total cache hits', ['cache_level', 'namespace'])
CACHE_MISSES_TOTAL = Counter('cache_misses_total', 'Total cache misses', ['cache_level', 'namespace'])
CACHE_OPERATION_DURATION = Histogram('cache_operation_duration_seconds', 'Cache operation duration', ['operation', 'namespace'])
CACHE_SIZE_BYTES = Gauge('cache_size_bytes', 'Cache size in bytes', ['cache_level', 'namespace'])

logger = logging.getLogger(__name__)

class MultiLevelCache:
    """
    Sistema de cache inteligente con dos niveles:
    - L1: Memoria local (ultrarrápido, limitado)
    - L2: Redis (persistente, compartido entre instancias)
    """
    
    def __init__(self, redis_host='localhost', redis_port=6379, max_memory_items=1000):
        try:
            self.redis_client = redis.Redis(
                host=redis_host, 
                port=redis_port, 
                db=0,
                decode_responses=False,  # Mantenemos bytes para pickle
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test conexión Redis
            self.redis_client.ping()
            self.redis_available = True
            logger.info("✅ Redis cache conectado exitosamente")
        except Exception as e:
            logger.warning(f"⚠️ Redis no disponible, solo cache L1: {e}")
            self.redis_available = False
            
        # Cache L1 - Memoria local con LRU
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.access_order: Dict[str, float] = {}  # Para LRU
        self.max_memory_items = max_memory_items
        
        # Estadísticas internas
        self.stats = {
            'l1_hits': 0,
            'l1_misses': 0, 
            'l2_hits': 0,
            'l2_misses': 0,
            'total_operations': 0
        }
        
    def _generate_cache_key(self, namespace: str, key_data: Any) -> str:
        """Generar clave de cache con namespace y hash del contenido"""
        if isinstance(key_data, str):
            content_hash = hashlib.md5(key_data.encode()).hexdigest()[:12]
        else:
            content_hash = hashlib.md5(str(key_data).encode()).hexdigest()[:12]
        return f"{namespace}:{content_hash}"
    
    def _evict_lru_if_needed(self):
        """Evict elementos menos usados si excedemos límite de memoria"""
        if len(self.memory_cache) >= self.max_memory_items:
            # Encontrar el elemento menos usado recientemente
            lru_key = min(self.access_order.items(), key=lambda x: x[1])[0]
            if lru_key in self.memory_cache:
                del self.memory_cache[lru_key]
                del self.access_order[lru_key]
                logger.debug(f"🗑️ Evicted LRU cache entry: {lru_key}")
    
    def get(self, namespace: str, key_data: Any) -> Optional[Any]:
        """
        Obtener valor del cache con fallback L1 -> L2
        
        Args:
            namespace: Namespace del cache (hybrid, adaptive, declarative)
            key_data: Datos para generar la clave
            
        Returns:
            Valor cacheado o None si no existe
        """
        cache_key = self._generate_cache_key(namespace, key_data)
        start_time = time.time()
        
        try:
            # L1: Memoria local (más rápido)
            if cache_key in self.memory_cache:
                self.access_order[cache_key] = time.time()  # Actualizar LRU
                value = self.memory_cache[cache_key]['value']
                
                # Métricas
                CACHE_HITS_TOTAL.labels(cache_level='l1', namespace=namespace).inc()
                self.stats['l1_hits'] += 1
                
                logger.debug(f"✅ Cache L1 HIT: {namespace}:{cache_key[:8]}...")
                return value
            
            # L1 Miss
            CACHE_MISSES_TOTAL.labels(cache_level='l1', namespace=namespace).inc()
            self.stats['l1_misses'] += 1
            
            # L2: Redis (si disponible)
            if self.redis_available:
                try:
                    cached_bytes = self.redis_client.get(cache_key)
                    if cached_bytes:
                        value = pickle.loads(cached_bytes)
                        
                        # Promover a L1
                        self._evict_lru_if_needed()
                        self.memory_cache[cache_key] = {
                            'value': value,
                            'timestamp': time.time(),
                            'namespace': namespace
                        }
                        self.access_order[cache_key] = time.time()
                        
                        # Métricas
                        CACHE_HITS_TOTAL.labels(cache_level='l2', namespace=namespace).inc()
                        self.stats['l2_hits'] += 1
                        
                        logger.debug(f"✅ Cache L2 HIT (promoted to L1): {namespace}:{cache_key[:8]}...")
                        return value
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error accediendo Redis: {e}")
            
            # L2 Miss
            CACHE_MISSES_TOTAL.labels(cache_level='l2', namespace=namespace).inc()
            self.stats['l2_misses'] += 1
            
            logger.debug(f"❌ Cache MISS: {namespace}:{cache_key[:8]}...")
            return None
            
        finally:
            # Métricas de duración
            duration = time.time() - start_time
            CACHE_OPERATION_DURATION.labels(operation='get', namespace=namespace).observe(duration)
            self.stats['total_operations'] += 1
    
    def set(self, namespace: str, key_data: Any, value: Any, ttl: int = 3600):
        """
        Almacenar valor en ambos niveles de cache
        
        Args:
            namespace: Namespace del cache
            key_data: Datos para generar la clave
            value: Valor a cachear
            ttl: Time to live en segundos
        """
        cache_key = self._generate_cache_key(namespace, key_data)
        start_time = time.time()
        
        try:
            # L1: Memoria local
            self._evict_lru_if_needed()
            self.memory_cache[cache_key] = {
                'value': value,
                'timestamp': time.time(),
                'namespace': namespace,
                'ttl': ttl
            }
            self.access_order[cache_key] = time.time()
            
            # L2: Redis (si disponible)
            if self.redis_available:
                try:
                    pickled_value = pickle.dumps(value)
                    self.redis_client.setex(cache_key, ttl, pickled_value)
                    
                    # Actualizar métricas de tamaño
                    CACHE_SIZE_BYTES.labels(cache_level='l2', namespace=namespace).set(len(pickled_value))
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error guardando en Redis: {e}")
            
            # Métricas de tamaño L1
            l1_size = sum(len(str(item['value'])) for item in self.memory_cache.values())
            CACHE_SIZE_BYTES.labels(cache_level='l1', namespace=namespace).set(l1_size)
            
            logger.debug(f"💾 Cache SET: {namespace}:{cache_key[:8]}... (TTL: {ttl}s)")
            
        finally:
            duration = time.time() - start_time
            CACHE_OPERATION_DURATION.labels(operation='set', namespace=namespace).observe(duration)
    
    def invalidate_namespace(self, namespace: str):
        """Invalidar todas las entradas de un namespace específico"""
        start_time = time.time()
        
        try:
            # L1: Remover de memoria
            keys_to_remove = [
                key for key, data in self.memory_cache.items() 
                if data.get('namespace') == namespace
            ]
            
            for key in keys_to_remove:
                del self.memory_cache[key]
                if key in self.access_order:
                    del self.access_order[key]
            
            # L2: Redis (usar patrón)
            if self.redis_available:
                try:
                    pattern = f"{namespace}:*"
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        self.redis_client.delete(*keys)
                except Exception as e:
                    logger.warning(f"⚠️ Error invalidando namespace en Redis: {e}")
                    
            logger.info(f"🗑️ Invalidated namespace '{namespace}': {len(keys_to_remove)} L1 entries")
            
        finally:
            duration = time.time() - start_time
            CACHE_OPERATION_DURATION.labels(operation='invalidate', namespace=namespace).observe(duration)
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas detalladas del cache"""
        l1_hit_rate = (self.stats['l1_hits'] / max(1, self.stats['l1_hits'] + self.stats['l1_misses'])) * 100
        l2_hit_rate = (self.stats['l2_hits'] / max(1, self.stats['l2_hits'] + self.stats['l2_misses'])) * 100
        
        return {
            'l1_entries': len(self.memory_cache),
            'l1_hit_rate': round(l1_hit_rate, 2),
            'l2_hit_rate': round(l2_hit_rate, 2),
            'total_operations': self.stats['total_operations'],
            'redis_available': self.redis_available,
            'memory_usage_mb': sum(len(str(item)) for item in self.memory_cache.values()) / (1024*1024)
        }

# Singleton global para usar en toda la aplicación
_global_cache = None

def get_cache() -> MultiLevelCache:
    """Obtener instancia global del cache"""
    global _global_cache
    if _global_cache is None:
        _global_cache = MultiLevelCache()
    return _global_cache

def cached(namespace: str, ttl: int = 3600):
    """
    Decorator para cachear automáticamente resultados de funciones
    
    Usage:
        @cached('hybrid', ttl=1800)
        def expensive_function(param1, param2):
            # función costosa
            return result
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Generar clave basada en función y parámetros
            cache_key_data = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            
            # Intentar obtener del cache
            cached_result = cache.get(namespace, cache_key_data)
            if cached_result is not None:
                return cached_result
            
            # Ejecutar función y cachear resultado
            result = func(*args, **kwargs)
            cache.set(namespace, cache_key_data, result, ttl)
            
            return result
        return wrapper
    return decorator