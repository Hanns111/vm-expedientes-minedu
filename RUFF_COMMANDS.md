# 🎨 Guía de Comandos Ruff

## 🚀 Comandos de Una Pasada

### Formatear Todo el Proyecto
```bash
# Comando básico - formatear + corregir issues automáticamente
make format

# O directamente con Ruff
ruff format . && ruff check --fix .

# Script completo con estadísticas
python scripts/format_code.py --all
```

### Verificar Sin Modificar
```bash
# Solo verificar formato y linting
make check

# Verificar formato específicamente
ruff format --check --diff .

# Verificar linting específicamente  
ruff check --no-fix .
```

## 🔧 Comandos Específicos

### Solo Formateo
```bash
# Formatear código (equivalente a Black)
ruff format .

# Verificar formato sin modificar
ruff format --check .

# Ver diferencias que se aplicarían
ruff format --check --diff .
```

### Solo Linting
```bash
# Verificar problemas de código
ruff check .

# Corregir automáticamente
ruff check --fix .

# Mostrar estadísticas
ruff check --statistics .

# Formato específico de salida
ruff check --output-format=github .
ruff check --output-format=json .
```

## 🎛️ Comandos del Makefile

### Comandos Principales
```bash
make help           # Ver todos los comandos disponibles
make dev-install    # Instalar todo para desarrollo
make format         # Formatear código
make lint           # Verificar linting
make all            # Ejecutar todo (format + lint + tipos + seguridad)
make check          # Verificar sin modificar
make test           # Ejecutar tests
make ci             # Pipeline completo local
```

### Comandos de Verificación
```bash
make format-check   # Solo verificar formato
make lint-check     # Solo verificar linting
make type-check     # Verificar tipos (MyPy)
make security       # Análisis de seguridad (Bandit)
```

## 🐍 Script Python Avanzado

### Uso Básico
```bash
# Formatear + estadísticas
python scripts/format_code.py --stats

# Solo verificar
python scripts/format_code.py --check

# Todas las verificaciones
python scripts/format_code.py --all

# Solo seguridad
python scripts/format_code.py --security
```

### Opciones Disponibles
```bash
python scripts/format_code.py --help

Opciones:
  --check          Solo verificar, no modificar
  --fix            Aplicar correcciones (por defecto)
  --stats          Mostrar estadísticas detalladas
  --security       Análisis de seguridad con Bandit
  --types          Verificación de tipos con MyPy
  --tests          Ejecutar tests
  --all            Todas las verificaciones
```

## 🔄 Pre-commit Hooks

### Instalar
```bash
make pre-commit-install

# O directamente
pre-commit install
```

### Ejecutar Manualmente
```bash
# Ejecutar hooks en todos los archivos
pre-commit run --all-files

# Ejecutar hook específico
pre-commit run ruff --all-files
pre-commit run ruff-format --all-files
```

## 📊 Configuración Avanzada

### Configurar por Proyecto
```bash
# Crear configuración personalizada
cat > .ruff.toml << EOF
line-length = 100
target-version = "py39"

[lint]
select = ["E", "F", "I", "N", "D"]
ignore = ["D107", "D203", "D213"]
EOF
```

### Ignorar Archivos Específicos
```bash
# En pyproject.toml
[tool.ruff]
exclude = [
    "migrations",
    "old_code",
    "legacy",
]

# O por línea en código
# ruff: noqa
# ruff: noqa: E501
```

## 🚨 Comandos de Emergencia

### Formatear Solo Archivos Modificados
```bash
# Git - solo archivos modificados
git diff --name-only --diff-filter=ACMR "*.py" | xargs ruff format
git diff --name-only --diff-filter=ACMR "*.py" | xargs ruff check --fix

# Git - archivos en staging
git diff --cached --name-only --diff-filter=ACMR "*.py" | xargs ruff format
```

### Ignorar Temporalmente
```bash
# Ignorar archivo específico
ruff check . --ignore-path path/to/file.py

# Ejecutar con warnings como errores
ruff check . --no-fix --exit-non-zero-on-fix
```

## ⚡ Comandos de CI/CD

### GitHub Actions
```yaml
# En workflow
- name: Run Ruff
  run: |
    ruff check . --output-format=github
    ruff format --check .
```

### Local CI Simulation
```bash
# Simular pipeline de CI localmente
make ci

# O paso a paso
make clean
make format-check
make lint-check
make type-check
make test
```

## 📈 Métricas y Reportes

### Estadísticas de Código
```bash
# Contar issues por regla
ruff check . --statistics

# Exportar reporte JSON
ruff check . --output-format=json > ruff-report.json

# Ver solo errores críticos
ruff check . --select=E,F --statistics
```

### Integración con Herramientas
```bash
# Pre-commit con Ruff
echo "repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
      - id: ruff-format" > .pre-commit-config.yaml

# VS Code settings.json
echo '{
  "python.linting.enabled": false,
  "ruff.enable": true,
  "ruff.organizeImports": true
}' > .vscode/settings.json
```

## 🎯 Casos de Uso Comunes

### Antes de Commit
```bash
make pre-commit
# o
python scripts/format_code.py --check --stats
```

### Deploy a Producción
```bash
make ci
# o
python scripts/format_code.py --all
```

### Revisión de Código
```bash
make check
# o
ruff check --output-format=github . > review.txt
```

### Setup Nuevo Desarrollador
```bash
make dev-setup
# o
pip install -e ".[dev]"
make pre-commit-install
make format
```

---

## 📋 Resumen de Migración de Black

### ✅ Completado
- ❌ **Black eliminado** de todas las configuraciones
- ✅ **Ruff configurado** como formateador único
- ✅ **pyproject.toml** completamente actualizado
- ✅ **GitHub Actions** migrados a Ruff
- ✅ **Pre-commit hooks** actualizados
- ✅ **Makefile** con comandos Ruff
- ✅ **Scripts Python** para automatización

### 🚀 Beneficios Obtenidos
- **Velocidad**: Ruff es ~10-100x más rápido que Black + flake8
- **Unificación**: Un solo tool para format + lint
- **Configuración**: Todo en pyproject.toml
- **Compatibilidad**: Drop-in replacement para Black
- **Más reglas**: 800+ reglas de linting incluidas

### ⚡ Comando Principal
```bash
# Todo en uno - formatear proyecto completo
make format

# Verificar antes de commit
make pre-commit

# Pipeline completo
make ci
```