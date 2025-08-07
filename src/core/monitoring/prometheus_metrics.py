#!/usr/bin/env python3
"""
Prometheus Metrics for MINEDU Backend
Provides comprehensive metrics collection for monitoring
"""

import time
import logging
from typing import Dict, Any, Optional
from functools import wraps
from pathlib import Path
import psutil
import gc

try:
    from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger('minedu.metrics')

class MinEducMetrics:
    """Centralized metrics collection for MINEDU system"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        if not PROMETHEUS_AVAILABLE:
            logger.warning("⚠️ Prometheus client not available")
            return
        
        self.registry = registry or CollectorRegistry()
        self._setup_metrics()
        logger.info("📊 Prometheus metrics initialized")
    
    def _setup_metrics(self):
        """Setup all Prometheus metrics"""
        
        # Application info
        self.app_info = Info(
            'minedu_app_info', 
            'Application information',
            registry=self.registry
        )
        self.app_info.info({
            'version': '2.0.0-performance',
            'environment': 'production',
            'service': 'minedu-backend'
        })
        
        # HTTP Request metrics
        self.http_requests_total = Counter(
            'minedu_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.http_request_duration = Histogram(
            'minedu_http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # Search metrics
        self.search_requests_total = Counter(
            'minedu_search_requests_total',
            'Total search requests',
            ['method', 'status'],
            registry=self.registry
        )
        
        self.search_duration = Histogram(
            'minedu_search_duration_seconds',
            'Search request duration in seconds',
            ['method'],
            buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
            registry=self.registry
        )
        
        self.search_results_count = Histogram(
            'minedu_search_results_count',
            'Number of search results returned',
            ['method'],
            buckets=(1, 5, 10, 20, 50, 100),
            registry=self.registry
        )
        
        # Document processing metrics
        self.document_uploads_total = Counter(
            'minedu_document_uploads_total',
            'Total document uploads',
            ['file_type', 'status'],
            registry=self.registry
        )
        
        self.document_processing_duration = Histogram(
            'minedu_document_processing_duration_seconds',
            'Document processing duration in seconds',
            ['file_type'],
            buckets=(1.0, 5.0, 15.0, 30.0, 60.0, 120.0),
            registry=self.registry
        )
        
        self.document_size_bytes = Histogram(
            'minedu_document_size_bytes',
            'Size of uploaded documents in bytes',
            ['file_type'],
            buckets=(1024, 10240, 102400, 1048576, 10485760, 104857600),  # 1KB to 100MB
            registry=self.registry
        )
        
        # ML Model metrics
        self.model_load_duration = Histogram(
            'minedu_model_load_duration_seconds',
            'Model loading duration in seconds',
            ['model_name', 'model_type'],
            registry=self.registry
        )
        
        self.model_inference_duration = Histogram(
            'minedu_model_inference_duration_seconds',
            'Model inference duration in seconds',
            ['model_name', 'model_type'],
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0),
            registry=self.registry
        )
        
        self.models_loaded = Gauge(
            'minedu_models_loaded',
            'Number of loaded ML models',
            registry=self.registry
        )
        
        self.model_memory_bytes = Gauge(
            'minedu_model_memory_bytes',
            'Memory usage by ML models in bytes',
            ['model_name', 'model_type'],
            registry=self.registry
        )
        
        # System resource metrics
        self.system_cpu_percent = Gauge(
            'minedu_system_cpu_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        self.system_memory_percent = Gauge(
            'minedu_system_memory_percent',
            'System memory usage percentage',
            registry=self.registry
        )
        
        self.system_memory_bytes = Gauge(
            'minedu_system_memory_bytes',
            'System memory usage in bytes',
            ['type'],  # 'used', 'available', 'total'
            registry=self.registry
        )
        
        self.process_memory_bytes = Gauge(
            'minedu_process_memory_bytes',
            'Process memory usage in bytes',
            ['type'],  # 'rss', 'vms'
            registry=self.registry
        )
        
        self.disk_usage_percent = Gauge(
            'minedu_disk_usage_percent',
            'Disk usage percentage',
            ['mount_point'],
            registry=self.registry
        )
        
        # Cache metrics (Redis)
        self.cache_operations_total = Counter(
            'minedu_cache_operations_total',
            'Total cache operations',
            ['operation', 'status'],  # get/set/delete, hit/miss/error
            registry=self.registry
        )
        
        self.cache_operation_duration = Histogram(
            'minedu_cache_operation_duration_seconds',
            'Cache operation duration in seconds',
            ['operation'],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25),
            registry=self.registry
        )
        
        # Application health metrics
        self.uptime_seconds = Gauge(
            'minedu_uptime_seconds',
            'Application uptime in seconds',
            registry=self.registry
        )
        
        self.health_check_status = Gauge(
            'minedu_health_check_status',
            'Health check status (1=healthy, 0=unhealthy)',
            ['component'],
            registry=self.registry
        )
        
        # Error metrics
        self.errors_total = Counter(
            'minedu_errors_total',
            'Total application errors',
            ['component', 'error_type'],
            registry=self.registry
        )

    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.http_requests_total.labels(
            method=method, 
            endpoint=endpoint, 
            status=f"{status_code//100}xx"
        ).inc()
        
        self.http_request_duration.labels(
            method=method, 
            endpoint=endpoint
        ).observe(duration)

    def record_search_request(self, method: str, duration: float, result_count: int, success: bool):
        """Record search request metrics"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        status = "success" if success else "error"
        
        self.search_requests_total.labels(method=method, status=status).inc()
        self.search_duration.labels(method=method).observe(duration)
        
        if success:
            self.search_results_count.labels(method=method).observe(result_count)

    def record_document_upload(self, file_type: str, file_size: int, processing_time: float, success: bool):
        """Record document upload and processing metrics"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        status = "success" if success else "error"
        
        self.document_uploads_total.labels(file_type=file_type, status=status).inc()
        self.document_size_bytes.labels(file_type=file_type).observe(file_size)
        
        if success:
            self.document_processing_duration.labels(file_type=file_type).observe(processing_time)

    def record_model_load(self, model_name: str, model_type: str, load_time: float):
        """Record model loading metrics"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.model_load_duration.labels(
            model_name=model_name, 
            model_type=model_type
        ).observe(load_time)

    def record_model_inference(self, model_name: str, model_type: str, inference_time: float):
        """Record model inference metrics"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.model_inference_duration.labels(
            model_name=model_name, 
            model_type=model_type
        ).observe(inference_time)

    def update_model_memory(self, model_name: str, model_type: str, memory_bytes: float):
        """Update model memory usage metrics"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.model_memory_bytes.labels(
            model_name=model_name, 
            model_type=model_type
        ).set(memory_bytes)

    def record_cache_operation(self, operation: str, duration: float, success: bool):
        """Record cache operation metrics"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        status = "hit" if success and operation == "get" else ("success" if success else "error")
        
        self.cache_operations_total.labels(operation=operation, status=status).inc()
        self.cache_operation_duration.labels(operation=operation).observe(duration)

    def record_error(self, component: str, error_type: str):
        """Record application errors"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.errors_total.labels(component=component, error_type=error_type).inc()

    def update_system_metrics(self):
        """Update system resource metrics"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_cpu_percent.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.system_memory_percent.set(memory.percent)
            self.system_memory_bytes.labels(type="used").set(memory.used)
            self.system_memory_bytes.labels(type="available").set(memory.available)
            self.system_memory_bytes.labels(type="total").set(memory.total)
            
            # Process memory
            process = psutil.Process()
            process_memory = process.memory_info()
            self.process_memory_bytes.labels(type="rss").set(process_memory.rss)
            self.process_memory_bytes.labels(type="vms").set(process_memory.vms)
            
            # Disk usage
            disk_usage = psutil.disk_usage('/')
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            self.disk_usage_percent.labels(mount_point="/").set(disk_percent)
            
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
            self.record_error("metrics", "system_update_failed")

    def update_health_status(self, component: str, healthy: bool):
        """Update component health status"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.health_check_status.labels(component=component).set(1 if healthy else 0)

    def update_uptime(self, start_time: float):
        """Update application uptime"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        uptime = time.time() - start_time
        self.uptime_seconds.set(uptime)

    def update_models_count(self, count: int):
        """Update loaded models count"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.models_loaded.set(count)

    def get_metrics_text(self) -> str:
        """Get metrics in Prometheus text format"""
        if not PROMETHEUS_AVAILABLE:
            return "# Prometheus client not available\n"
        
        return generate_latest(self.registry).decode('utf-8')

# Global metrics instance
_metrics = None

def get_metrics() -> MinEducMetrics:
    """Get global metrics instance"""
    global _metrics
    if _metrics is None:
        _metrics = MinEducMetrics()
    return _metrics

def track_request_metrics(endpoint_name: str):
    """Decorator to track HTTP request metrics"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            metrics = get_metrics()
            start_time = time.time()
            
            try:
                # Execute the function
                result = await func(*args, **kwargs)
                
                # Record success metrics
                duration = time.time() - start_time
                metrics.record_http_request("POST", endpoint_name, 200, duration)
                
                return result
                
            except Exception as e:
                # Record error metrics
                duration = time.time() - start_time
                status_code = getattr(e, 'status_code', 500)
                metrics.record_http_request("POST", endpoint_name, status_code, duration)
                metrics.record_error("api", type(e).__name__)
                raise
        
        return wrapper
    return decorator

def track_search_metrics(search_method: str):
    """Decorator to track search request metrics"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            metrics = get_metrics()
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                # Extract metrics from result
                duration = time.time() - start_time
                result_count = len(result.get('results', [])) if isinstance(result, dict) else 0
                
                metrics.record_search_request(search_method, duration, result_count, True)
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                metrics.record_search_request(search_method, duration, 0, False)
                metrics.record_error("search", type(e).__name__)
                raise
        
        return wrapper
    return decorator