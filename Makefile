# Makefile para el Sistema de Búsqueda Híbrido MINEDU

.PHONY: install setup test clean run-demo security-audit security-fix format lint all

# Comandos básicos
install:
	pip install -r requirements.txt
	pip install python-magic-bin  # Para Windows
	python -m spacy download es_core_news_sm

setup:
	python setup_project.py
	python src/core/path_migration.py

test:
	pytest tests/ -v --cov=src --cov-report=html

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov

# Comandos de seguridad
security-audit:
	@echo "🔒 Ejecutando auditoría de seguridad..."
	python security_audit.py --path .

security-fix:
	@echo "🔧 Aplicando correcciones de seguridad..."
	# Migrar rutas hardcodeadas
	python src/core/path_migration.py
	# Verificar permisos de archivos sensibles
	chmod 600 .env 2>/dev/null || true
	chmod 600 *.key 2>/dev/null || true
	# Limpiar logs antiguos
	find logs/ -name "*.log" -mtime +30 -delete 2>/dev/null || true

security-monitor:
	@echo "📊 Estado del monitor de seguridad..."
	python -c "from src.core.security.monitor import security_monitor; print(security_monitor.get_security_status())"

# Comandos de calidad
format:
	black src/ tests/ --line-length 100
	isort src/ tests/

lint:
	flake8 src/ tests/ --max-line-length=100 --ignore=E203,W503
	mypy src/ --ignore-missing-imports

# Demo
run-demo:
	python demo.py "¿Cuál es el monto máximo para viáticos?"

run-demo-secure:
	python demo_secure.py "¿Cuál es el monto máximo para viáticos?"

# Comando completo
all: security-audit format lint test

# Instalación de herramientas de seguridad
install-security-tools:
	pip install bandit safety pip-audit
	@echo "✅ Herramientas de seguridad instaladas"

# Escaneo de vulnerabilidades
security-scan:
	@echo "🔍 Escaneando código con bandit..."
	bandit -r src/ -f json -o bandit_report.json
	@echo "🔍 Verificando dependencias con safety..."
	safety check --json --output safety_report.json
	@echo "🔍 Auditando paquetes con pip-audit..."
	pip-audit --format json --output pip_audit_report.json
	@echo "✅ Escaneo completado. Revisa los reportes generados."

generate-vectorstores:
	python src/data_pipeline/generate_vectorstores.py

full-setup: install setup generate-vectorstores
