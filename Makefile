# Makefile para el Sistema de IA Gubernamental

# Variables
PYTHON := python3
PIP := pip
RUFF := ruff
PYTEST := pytest
MYPY := mypy

# Phony targets
.PHONY: install setup test clean run-demo format lint check security all \
        dev-install format-check lint-check type-check pre-commit-install \
        generate-vectorstores full-setup help

# Default target
help:
	@echo "🏛️  Sistema de IA Gubernamental - Comandos Disponibles"
	@echo "=================================================="
	@echo ""
	@echo "📦 INSTALACIÓN:"
	@echo "  install              Instalar dependencias básicas"
	@echo "  dev-install          Instalar dependencias de desarrollo"
	@echo "  setup                Configuración inicial del proyecto"
	@echo "  full-setup           Instalación + configuración completa"
	@echo ""
	@echo "🎨 CALIDAD DE CÓDIGO:"
	@echo "  format               Formatear código con Ruff"
	@echo "  format-check         Verificar formato sin modificar"
	@echo "  lint                 Ejecutar linter (Ruff + MyPy)"
	@echo "  lint-check           Verificar linting sin corregir"
	@echo "  type-check           Verificar tipos con MyPy"
	@echo "  security             Análisis de seguridad con Bandit"
	@echo "  check                Verificar todo (formato + lint + tipos)"
	@echo "  all                  Formatear + lint + tipos + seguridad"
	@echo ""
	@echo "🧪 TESTING:"
	@echo "  test                 Ejecutar tests con coverage"
	@echo "  test-fast            Ejecutar tests básicos (sin coverage)"
	@echo ""
	@echo "🚀 EJECUCIÓN:"
	@echo "  run-demo             Ejecutar demo básico"
	@echo "  run-demo-secure      Ejecutar demo seguro"
	@echo "  run-performance      Ejecutar demo de rendimiento"
	@echo ""
	@echo "🧹 LIMPIEZA:"
	@echo "  clean                Limpiar archivos temporales"
	@echo "  clean-cache          Limpiar cache de herramientas"
	@echo ""

# ============================================================================
# INSTALACIÓN
# ============================================================================

install:
	@echo "📦 Instalando dependencias básicas..."
	$(PIP) install -e .
	$(PYTHON) -m spacy download es_core_news_sm

dev-install:
	@echo "📦 Instalando dependencias de desarrollo..."
	$(PIP) install -e ".[dev,performance,ai]"
	$(PYTHON) -m spacy download es_core_news_sm
	@echo "✅ Instalación de desarrollo completada"

setup:
	@echo "⚙️ Configurando proyecto..."
	$(PYTHON) setup_project.py

pre-commit-install:
	@echo "🔗 Instalando pre-commit hooks..."
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "✅ Pre-commit hooks instalados"

# ============================================================================
# FORMATEO Y LINTING CON RUFF
# ============================================================================

format:
	@echo "🎨 Formateando código con Ruff..."
	$(RUFF) format .
	$(RUFF) check --fix .
	@echo "✅ Código formateado exitosamente"

format-check:
	@echo "🔍 Verificando formato del código..."
	$(RUFF) format --check --diff .
	@echo "✅ Verificación de formato completada"

lint:
	@echo "🔍 Ejecutando linter..."
	$(RUFF) check .
	@echo "✅ Linting completado"

lint-check:
	@echo "🔍 Verificando linting sin corregir..."
	$(RUFF) check --no-fix .

lint-fix:
	@echo "🔧 Aplicando correcciones automáticas..."
	$(RUFF) check --fix .
	@echo "✅ Correcciones aplicadas"

type-check:
	@echo "🔬 Verificando tipos con MyPy..."
	$(MYPY) --config-file=pyproject.toml src/ backend/ || true
	@echo "✅ Verificación de tipos completada"

security:
	@echo "🔒 Ejecutando análisis de seguridad..."
	bandit -r src/ backend/ -f txt --severity-level medium || true
	@echo "✅ Análisis de seguridad completado"

# ============================================================================
# VERIFICACIONES COMBINADAS
# ============================================================================

check: format-check lint-check type-check
	@echo "✅ Todas las verificaciones completadas"

all: format lint type-check security
	@echo "🎉 Todas las herramientas ejecutadas exitosamente"

# Alias para el script Python completo
format-all:
	@echo "🚀 Ejecutando formateador completo..."
	$(PYTHON) scripts/format_code.py --all
	@echo "✅ Formateo completo terminado"

# ============================================================================
# TESTING
# ============================================================================

test:
	@echo "🧪 Ejecutando tests con coverage..."
	$(PYTEST) --cov --cov-report=term-missing --cov-report=html
	@echo "✅ Tests completados"

test-fast:
	@echo "⚡ Ejecutando tests rápidos..."
	$(PYTEST) --tb=short -q
	@echo "✅ Tests rápidos completados"

test-integration:
	@echo "🔗 Ejecutando tests de integración..."
	$(PYTEST) -m integration -v
	@echo "✅ Tests de integración completados"

test-unit:
	@echo "🔬 Ejecutando tests unitarios..."
	$(PYTEST) -m "not integration" -v
	@echo "✅ Tests unitarios completados"

# ============================================================================
# EJECUCIÓN
# ============================================================================

run-demo:
	@echo "🎯 Ejecutando demo básico..."
	$(PYTHON) demo.py "¿Cuál es el monto máximo para viáticos?"

run-demo-secure:
	@echo "🔒 Ejecutando demo seguro..."
	$(PYTHON) demo_secure.py "¿Cuál es el tope máximo para declaración jurada?"

run-performance:
	@echo "⚡ Ejecutando demo de rendimiento..."
	streamlit run demo_performance.py --server.port 8501

# ============================================================================
# GENERACIÓN DE DATOS
# ============================================================================

generate-vectorstores:
	@echo "🔍 Generando vectorstores..."
	$(PYTHON) src/data_pipeline/generate_vectorstores.py
	@echo "✅ Vectorstores generados"

# ============================================================================
# LIMPIEZA
# ============================================================================

clean:
	@echo "🧹 Limpiando archivos temporales..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf build/
	rm -rf dist/
	@echo "✅ Limpieza completada"

clean-cache:
	@echo "🧹 Limpiando cache de herramientas..."
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/
	rm -rf __pycache__/
	find . -name ".ruff_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cache limpiado"

# ============================================================================
# TARGETS COMBINADOS
# ============================================================================

# Setup completo para desarrollo
dev-setup: dev-install pre-commit-install setup
	@echo "🎉 Setup de desarrollo completado"

# Setup completo para producción  
full-setup: install setup generate-vectorstores
	@echo "🎉 Setup completo terminado"

# Pipeline de CI/CD local
ci: clean format-check lint-check type-check test
	@echo "🎉 Pipeline CI/CD local completado"

# Preparar para commit
pre-commit: format lint test-fast
	@echo "✅ Código listo para commit"
