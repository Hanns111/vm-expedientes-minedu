#!/bin/bash

# 🚨 SCRIPT DE VERIFICACIÓN ANTIALUCINACIONES
# Proyecto: VM-EXPEDIENTES-MINEDU
# Objetivo: Detectar automáticamente simulaciones y datos falsos
# Uso: Ejecutar diariamente en CI/CD y antes de deployments

set -e

echo "🔍 INICIANDO VERIFICACIÓN ANTIALUCINACIONES - $(date)"
echo "=================================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Contadores
CRITICAL_ISSUES=0
WARNING_ISSUES=0

# Función para logs críticos
log_critical() {
    echo -e "${RED}❌ CRÍTICO: $1${NC}"
    ((CRITICAL_ISSUES++))
}

# Función para warnings
log_warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
    ((WARNING_ISSUES++))
}

# Función para logs de éxito
log_success() {
    echo -e "${GREEN}✅ OK: $1${NC}"
}

echo "🔍 1. VERIFICANDO FUNCIONES DE SIMULACIÓN..."
echo "--------------------------------------------"

# Buscar funciones de simulación prohibidas
SIMULATION_FUNCTIONS=$(grep -r "def.*simul" --include="*.py" . --exclude-dir=venv --exclude-dir=.git --exclude-dir=__pycache__ 2>/dev/null || true)

if [ -n "$SIMULATION_FUNCTIONS" ]; then
    log_critical "Funciones de simulación encontradas:"
    echo "$SIMULATION_FUNCTIONS"
else
    log_success "No se encontraron funciones de simulación"
fi

echo ""
echo "🔍 2. VERIFICANDO DATOS HARDCODEADOS..."
echo "---------------------------------------"

# Buscar montos hardcodeados sospechosos
HARDCODED_AMOUNTS=$(grep -rE "S/\s*[0-9]+\.[0-9]{2}|USD\s*[0-9]+|EUR\s*[0-9]+" --include="*.py" . --exclude-dir=venv --exclude-dir=.git --exclude-dir=__pycache__ 2>/dev/null || true)

if [ -n "$HARDCODED_AMOUNTS" ]; then
    log_critical "Montos hardcodeados encontrados:"
    echo "$HARDCODED_AMOUNTS"
else
    log_success "No se encontraron montos hardcodeados"
fi

echo ""
echo "🔍 3. VERIFICANDO CARGOS GUBERNAMENTALES FALSOS..."
echo "------------------------------------------------"

# Buscar cargos gubernamentales hardcodeados
FAKE_POSITIONS=$(grep -rE "Ministro|Funcionario|Director.*General" --include="*.py" . --exclude-dir=venv --exclude-dir=.git --exclude-dir=__pycache__ --exclude="*.md" 2>/dev/null || true)

if [ -n "$FAKE_POSITIONS" ]; then
    log_warning "Posibles cargos hardcodeados encontrados (revisar contexto):"
    echo "$FAKE_POSITIONS"
else
    log_success "No se encontraron cargos hardcodeados"
fi

echo ""
echo "🔍 4. VERIFICANDO TABLAS SIMULADAS..."
echo "------------------------------------"

# Buscar indicios de tablas simuladas
SIMULATED_TABLES=$(grep -rE "concepto.*monto|funcionario.*cargo|presupuesto.*[0-9]" --include="*.py" . --exclude-dir=venv --exclude-dir=.git --exclude-dir=__pycache__ 2>/dev/null || true)

if [ -n "$SIMULATED_TABLES" ]; then
    log_critical "Posibles tablas simuladas encontradas:"
    echo "$SIMULATED_TABLES"
else
    log_success "No se encontraron tablas simuladas"
fi

echo ""
echo "🔍 5. VERIFICANDO RETORNOS SEGUROS..."
echo "------------------------------------"

# Verificar que existan funciones de extracción real
REAL_EXTRACTION=$(grep -r "_real_.*extraction\|extract_.*real" --include="*.py" . --exclude-dir=venv --exclude-dir=.git --exclude-dir=__pycache__ 2>/dev/null || true)

if [ -n "$REAL_EXTRACTION" ]; then
    log_success "Funciones de extracción real encontradas"
else
    log_warning "No se encontraron funciones de extracción real implementadas"
fi

echo ""
echo "🔍 6. VERIFICANDO LOGGING DE AUDITORÍA..."
echo "----------------------------------------"

# Verificar que exista logging crítico
AUDIT_LOGGING=$(grep -r "logger.*error\|logger.*critical\|AUDIT" --include="*.py" . --exclude-dir=venv --exclude-dir=.git --exclude-dir=__pycache__ 2>/dev/null || true)

if [ -n "$AUDIT_LOGGING" ]; then
    log_success "Sistema de logging de auditoría presente"
else
    log_warning "Falta sistema de logging de auditoría"
fi

echo ""
echo "🔍 7. VERIFICANDO DOCUMENTACIÓN ANTIALUCINACIONES..."
echo "---------------------------------------------------"

# Verificar que existe documentación
if [ -f "docs/ANTI_ALUCINACIONES_PERMANENTE.md" ]; then
    log_success "Documentación antialucinaciones presente"
else
    log_critical "Falta documentación antialucinaciones permanente"
fi

if [ -f "CONTEXTO_ANTIALUCINACIONES_FINAL.md" ]; then
    log_success "Contexto antialucinaciones presente"
else
    log_warning "Falta archivo de contexto antialucinaciones"
fi

echo ""
echo "🔍 8. VERIFICANDO IMPORTS SEGUROS..."
echo "-----------------------------------"

# Verificar imports de bibliotecas seguras para extracción
SAFE_IMPORTS=$(grep -rE "import.*camelot|import.*pdfplumber|import.*PyMuPDF|import.*fitz" --include="*.py" . --exclude-dir=venv --exclude-dir=.git --exclude-dir=__pycache__ 2>/dev/null || true)

if [ -n "$SAFE_IMPORTS" ]; then
    log_success "Bibliotecas seguras de extracción importadas"
else
    log_warning "Faltan imports de bibliotecas seguras (camelot, pdfplumber, etc.)"
fi

echo ""
echo "🔍 9. VERIFICANDO ARCHIVOS CRÍTICOS..."
echo "-------------------------------------"

# Lista de archivos críticos que deben estar presentes
CRITICAL_FILES=(
    "docs/ANTI_ALUCINACIONES_PERMANENTE.md"
    "CHANGELOG.md"
    "requirements.txt"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        log_success "Archivo crítico presente: $file"
    else
        log_critical "Archivo crítico faltante: $file"
    fi
done

echo ""
echo "🔍 10. VERIFICANDO PATRONES SOSPECHOSOS ADICIONALES..."
echo "-----------------------------------------------------"

# Buscar otros patrones sospechosos
SUSPICIOUS_PATTERNS=$(grep -rE "fake|mock|dummy|test.*data.*[0-9]" --include="*.py" . --exclude-dir=venv --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=tests 2>/dev/null || true)

if [ -n "$SUSPICIOUS_PATTERNS" ]; then
    log_warning "Patrones sospechosos encontrados (revisar contexto):"
    echo "$SUSPICIOUS_PATTERNS"
else
    log_success "No se encontraron patrones sospechosos adicionales"
fi

echo ""
echo "=================================================="
echo "📊 RESUMEN DE VERIFICACIÓN ANTIALUCINACIONES"
echo "=================================================="

echo "🗓️  Fecha: $(date)"
echo "📁 Directorio: $(pwd)"
echo "🔍 Archivos escaneados: $(find . -name "*.py" -not -path "./venv/*" -not -path "./.git/*" | wc -l)"

echo ""
echo "📊 RESULTADOS:"
echo "--------------"

if [ $CRITICAL_ISSUES -eq 0 ]; then
    echo -e "${GREEN}✅ CRÍTICOS: $CRITICAL_ISSUES (SISTEMA SEGURO)${NC}"
else
    echo -e "${RED}❌ CRÍTICOS: $CRITICAL_ISSUES (REQUIERE ACCIÓN INMEDIATA)${NC}"
fi

if [ $WARNING_ISSUES -eq 0 ]; then
    echo -e "${GREEN}✅ WARNINGS: $WARNING_ISSUES${NC}"
else
    echo -e "${YELLOW}⚠️  WARNINGS: $WARNING_ISSUES (REVISAR)${NC}"
fi

echo ""
echo "🏛️ ESTADO FINAL:"
echo "----------------"

if [ $CRITICAL_ISSUES -eq 0 ]; then
    echo -e "${GREEN}✅ SISTEMA APTO PARA PRODUCCIÓN GUBERNAMENTAL${NC}"
    echo "✅ No se detectaron alucinaciones críticas"
    echo "✅ Sistema cumple con estándares de seguridad"
    EXIT_CODE=0
else
    echo -e "${RED}❌ SISTEMA NO APTO PARA PRODUCCIÓN${NC}"
    echo "❌ Se detectaron problemas críticos de alucinación"
    echo "❌ REQUIERE CORRECCIÓN INMEDIATA antes de deployment"
    EXIT_CODE=1
fi

echo ""
echo "📋 PRÓXIMOS PASOS:"
echo "-----------------"

if [ $CRITICAL_ISSUES -gt 0 ]; then
    echo "1. ❌ Corregir problemas críticos listados arriba"
    echo "2. ❌ Re-ejecutar verificación hasta 0 problemas críticos"
    echo "3. ❌ Solo entonces proceder con deployment"
else
    echo "1. ✅ Sistema verificado y seguro"
    echo "2. ✅ Proceder con confidence al deployment"
    echo "3. ✅ Programar próxima verificación en 24 horas"
fi

echo ""
echo "🔄 COMANDOS ÚTILES:"
echo "------------------"
echo "# Verificar cambios específicos:"
echo "git status --porcelain"
echo ""
echo "# Re-ejecutar verificación:"
echo "./scripts/verificacion_antialucinaciones.sh"
echo ""
echo "# Commit seguro (solo si 0 críticos):"
echo "git add . && git commit -m 'feat: sistema antialucinaciones v2.0.0'"

echo ""
echo "=================================================="
echo "🚨 VERIFICACIÓN ANTIALUCINACIONES COMPLETADA"
echo "=================================================="

# Log a archivo para auditoría
echo "$(date): CRITICAL=$CRITICAL_ISSUES, WARNING=$WARNING_ISSUES" >> logs/verificacion_antialucinaciones.log

exit $EXIT_CODE 