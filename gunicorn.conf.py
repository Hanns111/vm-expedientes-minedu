# Configuración de Gunicorn para VM-Expedientes-MINEDU
# Configuración optimizada para producción gubernamental

import multiprocessing
import os

# === CONFIGURACIÓN DE BINDING ===
bind = "0.0.0.0:8001"
backlog = 2048

# === CONFIGURACIÓN DE WORKERS ===
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# === CONFIGURACIÓN DE SEGURIDAD ===
# CORREGIDO: Solo permitir proxy desde localhost (no wildcard)
forwarded_allow_ips = "127.0.0.1"

# CORREGIDO: Desactivar debug verbose para producción
spew = False

# === CONFIGURACIÓN DE TIMEOUTS ===
timeout = 30
keepalive = 2
graceful_timeout = 30

# === CONFIGURACIÓN DE LOGGING ===
accesslog = "/var/log/minedu/gunicorn_access.log"
errorlog = "/var/log/minedu/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# === CONFIGURACIÓN DE USUARIO (PRODUCCIÓN) ===
# user = "minedu"
# group = "minedu"

# === CONFIGURACIÓN DE PROCESO ===
daemon = False
pidfile = "/var/run/minedu/gunicorn.pid"
tmp_upload_dir = "/tmp"

# === CONFIGURACIÓN DE SEGURIDAD ADICIONAL ===
# Preload de la aplicación para eficiencia
preload_app = True

# Límite de memoria
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# === CONFIGURACIÓN SSL (OPCIONAL) ===
# keyfile = "/etc/ssl/private/minedu.key"
# certfile = "/etc/ssl/certs/minedu.crt"
# ssl_version = 3
# ciphers = "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS"

# === HOOKS DE CONFIGURACIÓN ===
def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal") 