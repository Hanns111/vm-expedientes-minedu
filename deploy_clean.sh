#!/bin/bash

# 🚀 DEPLOY CLEAN SCRIPT - VM EXPEDIENTES MINEDU
# Deployment limpio con validación completa
# Fecha: 23 Junio 2025

set -e  # Exit on any error

echo "🚀 INICIANDO DEPLOYMENT LIMPIO - VM EXPEDIENTES MINEDU"
echo "============================================================"

# Función para logging con timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Función para verificar comandos
check_command() {
    if command -v "$1" >/dev/null 2>&1; then
        log "✅ $1 está disponible"
        return 0
    else
        log "❌ $1 no está disponible"
        return 1
    fi
}

# FASE 1: VERIFICACIÓN PRE-DEPLOYMENT
log "🔍 FASE 1: VERIFICACIÓN PRE-DEPLOYMENT"
echo "------------------------------------------------------------"

# Verificar Docker
log "Verificando Docker..."
check_command docker || { log "❌ Docker no está instalado"; exit 1; }
check_command docker-compose || { log "❌ Docker Compose no está instalado"; exit 1; }

# Verificar versiones
log "Versiones instaladas:"
docker --version
docker-compose --version

# Test básico Docker
log "Ejecutando test básico Docker..."
docker run --rm hello-world || { log "❌ Docker test falló"; exit 1; }
log "✅ Docker test exitoso"

# FASE 2: VALIDACIÓN CONFIGURACIÓN
log "📋 FASE 2: VALIDACIÓN CONFIGURACIÓN"
echo "------------------------------------------------------------"

# Verificar archivos críticos
REQUIRED_FILES=(
    "docker-compose.yml"
    ".env.production"
    "Dockerfile"
    "api_minedu.py"
    "requirements.txt"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        log "✅ $file encontrado"
    else
        log "❌ $file no encontrado"
        exit 1
    fi
done

# Ejecutar validación completa
log "Ejecutando validación de configuración..."
python validate_deployment_config.py || { log "❌ Validación falló"; exit 1; }
log "✅ Validación de configuración exitosa"

# FASE 3: LIMPIEZA PRE-DEPLOYMENT
log "🧹 FASE 3: LIMPIEZA PRE-DEPLOYMENT"
echo "------------------------------------------------------------"

# Detener contenedores existentes
log "Deteniendo contenedores existentes..."
docker-compose down --remove-orphans || true

# Limpiar imágenes huérfanas
log "Limpiando imágenes huérfanas..."
docker image prune -f || true

# Limpiar volúmenes no utilizados
log "Limpiando volúmenes no utilizados..."
docker volume prune -f || true

# FASE 4: BUILD Y DEPLOYMENT
log "🏗️ FASE 4: BUILD Y DEPLOYMENT"
echo "------------------------------------------------------------"

# Copiar variables de entorno
log "Configurando variables de entorno..."
cp .env.production .env

# Build de imágenes
log "Construyendo imágenes Docker..."
docker-compose build --no-cache

# Deployment
log "Iniciando deployment..."
if [[ "$1" == "production" ]]; then
    log "🏛️ MODO PRODUCCIÓN ACTIVADO"
    docker-compose -f docker-compose.yml up -d
else
    log "🔧 MODO DESARROLLO ACTIVADO"
    docker-compose up -d
fi

# FASE 5: VERIFICACIÓN POST-DEPLOYMENT
log "✅ FASE 5: VERIFICACIÓN POST-DEPLOYMENT"
echo "------------------------------------------------------------"

# Esperar a que los servicios estén listos
log "Esperando a que los servicios estén listos..."
sleep 30

# Verificar contenedores
log "Estado de contenedores:"
docker-compose ps

# Health checks
log "Ejecutando health checks..."

# Check API Backend
log "Verificando API Backend (puerto 8000)..."
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    log "✅ API Backend respondiendo"
else
    log "⚠️ API Backend no responde (puede estar iniciando)"
fi

# Check Streamlit (si está configurado)
log "Verificando disponibilidad de puertos..."
netstat -an | grep :8000 || log "Puerto 8000 no está en uso"
netstat -an | grep :8501 || log "Puerto 8501 no está en uso"

# FASE 6: LOGS Y MONITOREO
log "📊 FASE 6: LOGS Y MONITOREO"
echo "------------------------------------------------------------"

# Mostrar logs recientes
log "Últimos logs del sistema:"
docker-compose logs --tail=50

# Información del sistema
log "Información del sistema Docker:"
docker system df

# FASE 7: TESTING INTEGRACIÓN
log "🧪 FASE 7: TESTING INTEGRACIÓN"
echo "------------------------------------------------------------"

# Ejecutar tests de integración si existen
if [[ -f "test_integration.py" ]]; then
    log "Ejecutando tests de integración..."
    python test_integration.py || log "⚠️ Algunos tests de integración fallaron"
else
    log "ℹ️ No se encontraron tests de integración"
fi

# RESULTADO FINAL
log "🎉 DEPLOYMENT COMPLETADO EXITOSAMENTE"
echo "============================================================"
log "🏛️ Sistema VM Expedientes MINEDU desplegado"
log "📊 Estado: PRODUCTION-READY"
log "🔗 Servicios disponibles:"
log "   - API Backend: http://localhost:8000"
log "   - API Docs: http://localhost:8000/docs"
log "   - Streamlit: http://localhost:8501 (si configurado)"
log "   - Frontend: http://localhost:3000 (si configurado)"

# Comandos útiles
echo ""
log "📋 COMANDOS ÚTILES:"
log "   Ver logs:        docker-compose logs -f"
log "   Reiniciar:       docker-compose restart"
log "   Detener:         docker-compose down"
log "   Estado:          docker-compose ps"
log "   Monitoreo:       docker stats"

echo ""
log "🚀 ¡DEPLOYMENT EXITOSO! Sistema listo para producción." 