#!/usr/bin/env python3
"""
Servidor de Métricas Prometheus
==============================

Servidor standalone que expone métricas del sistema en formato Prometheus
para integración con Grafana y monitoreo en tiempo real.
"""

import time
import threading
from prometheus_client import start_http_server, Counter, Histogram, Gauge, generate_latest
from flask import Flask, Response
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Métricas globales del sistema
SYSTEM_UPTIME = Gauge('system_uptime_seconds', 'System uptime in seconds')
MEMORY_USAGE = Gauge('system_memory_usage_bytes', 'System memory usage in bytes')
CPU_USAGE = Gauge('system_cpu_usage_percent', 'System CPU usage percentage')

class MetricsServer:
    """Servidor de métricas con simulación de datos en tiempo real"""
    
    def __init__(self, port=8001):
        self.port = port
        self.start_time = time.time()
        self.running = False
        
        # Flask app para endpoint personalizado
        self.app = Flask(__name__)
        self.setup_routes()
        
    def setup_routes(self):
        """Configurar rutas Flask"""
        
        @self.app.route('/metrics')
        def metrics():
            """Endpoint de métricas compatible con Prometheus"""
            return Response(generate_latest(), mimetype='text/plain')
        
        @self.app.route('/health')
        def health():
            """Health check endpoint"""
            return {'status': 'healthy', 'uptime': time.time() - self.start_time}
    
    def update_system_metrics(self):
        """Actualizar métricas del sistema (simuladas)"""
        while self.running:
            try:
                # Simular métricas del sistema
                uptime = time.time() - self.start_time
                SYSTEM_UPTIME.set(uptime)
                
                # Simular uso de memoria (fluctuante)
                import random
                memory_usage = random.uniform(500_000_000, 2_000_000_000)  # 500MB - 2GB
                MEMORY_USAGE.set(memory_usage)
                
                # Simular uso de CPU
                cpu_usage = random.uniform(10, 80)  # 10-80%
                CPU_USAGE.set(cpu_usage)
                
                time.sleep(5)  # Actualizar cada 5 segundos
                
            except Exception as e:
                logger.error(f"Error actualizando métricas: {e}")
                time.sleep(10)
    
    def start(self):
        """Iniciar servidor de métricas"""
        self.running = True
        
        # Iniciar hilo de actualización de métricas
        metrics_thread = threading.Thread(target=self.update_system_metrics, daemon=True)
        metrics_thread.start()
        
        # Iniciar servidor Prometheus nativo
        try:
            start_http_server(self.port)
            logger.info(f"✅ Servidor Prometheus iniciado en puerto {self.port}")
        except Exception as e:
            logger.error(f"❌ Error iniciando servidor Prometheus: {e}")
        
        # Iniciar servidor Flask
        logger.info(f"🚀 Iniciando servidor de métricas en puerto {self.port + 1}")
        self.app.run(host='0.0.0.0', port=self.port + 1, debug=False)
    
    def stop(self):
        """Detener servidor"""
        self.running = False
        logger.info("🛑 Servidor de métricas detenido")

if __name__ == "__main__":
    server = MetricsServer()
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()