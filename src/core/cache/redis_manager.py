#!/usr/bin/env python3
"""
Redis Connection Pool Manager for MINEDU Backend
Implements connection pooling, caching, and session management
"""

import redis
import redis.sentinel
import json
import pickle
import hashlib
import asyncio
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
import logging
import os
from contextlib import asynccontextmanager
from functools import wraps

logger = logging.getLogger('minedu.cache')

class RedisManager:
    """Redis connection pool manager with advanced features"""
    
    def __init__(self, 
                 host: str = None,
                 port: int = None,
                 password: str = None,
                 db: int = 0,
                 max_connections: int = 50,
                 sentinel_hosts: List[str] = None,
                 master_name: str = 'mymaster'):
        
        self.host = host or os.getenv('REDIS_HOST', 'localhost')
        self.port = port or int(os.getenv('REDIS_PORT', 6379))
        self.password = password or os.getenv('REDIS_PASSWORD')
        self.db = db
        self.max_connections = max_connections
        self.sentinel_hosts = sentinel_hosts
        self.master_name = master_name
        
        # Connection pools
        self._pool = None
        self._sentinel = None
        self._redis_client = None
        
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize Redis connection with pooling"""
        try:
            if self.sentinel_hosts:
                # High Availability with Sentinel
                self._sentinel = redis.sentinel.Sentinel(
                    [(host, 26379) for host in self.sentinel_hosts],
                    socket_timeout=0.1
                )
                self._redis_client = self._sentinel.master_for(
                    self.master_name,
                    socket_timeout=0.1,
                    password=self.password,
                    db=self.db
                )
                logger.info("Redis Sentinel connection initialized")
            else:
                # Standard connection pool
                self._pool = redis.ConnectionPool(
                    host=self.host,
                    port=self.port,
                    password=self.password,
                    db=self.db,
                    max_connections=self.max_connections,
                    retry_on_timeout=True,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    health_check_interval=30
                )
                self._redis_client = redis.Redis(
                    connection_pool=self._pool,
                    decode_responses=True
                )
                logger.info(f"Redis pool initialized: {self.host}:{self.port}")
            
            # Test connection
            self._redis_client.ping()
            logger.info("Redis connection test successful")
            
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self._redis_client = None
    
    @property
    def client(self) -> redis.Redis:
        """Get Redis client with automatic reconnection"""
        if not self._redis_client:
            self._initialize_connection()
        return self._redis_client
    
    def get_pool_info(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        if self._pool:
            return {
                'created_connections': self._pool.created_connections,
                'available_connections': len(self._pool._available_connections),
                'in_use_connections': len(self._pool._in_use_connections),
                'max_connections': self.max_connections
            }
        return {'status': 'no_pool_info'}
    
    # Cache Operations
    def cache_set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set cache with TTL"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            elif not isinstance(value, str):
                value = pickle.dumps(value)
            
            return self.client.setex(key, ttl, value)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def cache_get(self, key: str) -> Optional[Any]:
        """Get cached value with automatic deserialization"""
        try:
            value = self.client.get(key)
            if value is None:
                return None
            
            # Try JSON first
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                pass
            
            # Try pickle
            try:
                return pickle.loads(value.encode() if isinstance(value, str) else value)
            except (pickle.PickleError, TypeError):
                pass
            
            # Return as string
            return value
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def cache_delete(self, key: str) -> bool:
        """Delete cache key"""
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def cache_exists(self, key: str) -> bool:
        """Check if cache key exists"""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False
    
    # Search Result Caching
    def cache_search_result(self, query: str, method: str, results: List[Dict], 
                          ttl: int = 1800):
        """Cache search results with query-specific key"""
        cache_key = self._generate_search_key(query, method)
        cache_data = {
            'query': query,
            'method': method,
            'results': results,
            'timestamp': datetime.utcnow().isoformat(),
            'ttl': ttl
        }
        return self.cache_set(cache_key, cache_data, ttl)
    
    def get_cached_search_result(self, query: str, method: str) -> Optional[Dict]:
        """Get cached search result"""
        cache_key = self._generate_search_key(query, method)
        return self.cache_get(cache_key)
    
    def _generate_search_key(self, query: str, method: str) -> str:
        """Generate consistent cache key for search queries"""
        query_hash = hashlib.md5(
            f"{query.lower().strip()}{method}".encode('utf-8')
        ).hexdigest()
        return f"search:{method}:{query_hash}"
    
    # Session Management
    def create_session(self, user_id: str, session_data: Dict, ttl: int = 3600) -> str:
        """Create user session"""
        session_id = hashlib.sha256(f"{user_id}{datetime.utcnow()}".encode()).hexdigest()
        session_key = f"session:{session_id}"
        
        session_data.update({
            'user_id': user_id,
            'created_at': datetime.utcnow().isoformat(),
            'last_activity': datetime.utcnow().isoformat()
        })
        
        if self.cache_set(session_key, session_data, ttl):
            return session_id
        return None
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        session_key = f"session:{session_id}"
        return self.cache_get(session_key)
    
    def update_session_activity(self, session_id: str):
        """Update session last activity"""
        session_key = f"session:{session_id}"
        session_data = self.cache_get(session_key)
        if session_data:
            session_data['last_activity'] = datetime.utcnow().isoformat()
            self.cache_set(session_key, session_data, 3600)
    
    # Rate Limiting
    def check_rate_limit(self, user_id: str, limit: int = 100, window: int = 3600) -> bool:
        """Check if user is within rate limits"""
        key = f"rate_limit:{user_id}"
        current = self.client.get(key)
        
        if current is None:
            self.client.setex(key, window, 1)
            return True
        
        if int(current) >= limit:
            return False
        
        self.client.incr(key)
        return True
    
    # Health Check
    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        try:
            start_time = datetime.utcnow()
            
            # Ping test
            self.client.ping()
            
            # Write/Read test
            test_key = "health_check_test"
            test_value = "ok"
            self.client.setex(test_key, 10, test_value)
            retrieved = self.client.get(test_key)
            self.client.delete(test_key)
            
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return {
                'status': 'healthy',
                'response_time_ms': response_time,
                'read_write_test': retrieved == test_value,
                'pool_info': self.get_pool_info(),
                'redis_info': {
                    'version': self.client.info()['redis_version'],
                    'memory_used': self.client.info()['used_memory_human'],
                    'connected_clients': self.client.info()['connected_clients']
                }
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'pool_info': self.get_pool_info()
            }
    
    def close(self):
        """Close all connections"""
        if self._pool:
            self._pool.disconnect()
            logger.info("Redis connection pool closed")

# Global Redis manager instance
redis_manager = None

def get_redis_manager() -> RedisManager:
    """Get global Redis manager instance"""
    global redis_manager
    if redis_manager is None:
        redis_manager = RedisManager()
    return redis_manager

def cache_search_results(ttl: int = 1800):
    """Decorator for caching search results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract query and method from args/kwargs
            query = kwargs.get('query') or (args[0] if args else '')
            method = kwargs.get('method', 'default')
            
            redis_mgr = get_redis_manager()
            
            # Try to get cached result
            cached_result = redis_mgr.get_cached_search_result(query, method)
            if cached_result:
                logger.info(f"Cache hit for query: {query[:50]}...")
                return cached_result['results']
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            redis_mgr.cache_search_result(query, method, result, ttl)
            
            logger.info(f"Cache miss, result cached for query: {query[:50]}...")
            return result
        
        return wrapper
    return decorator

# Example usage in FastAPI endpoint
@asynccontextmanager
async def redis_connection():
    """Context manager for Redis connections"""
    redis_mgr = get_redis_manager()
    try:
        yield redis_mgr
    finally:
        # Connection returned to pool automatically
        pass