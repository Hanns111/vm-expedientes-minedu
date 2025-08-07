# ✅ CHECKLIST DEPLOYMENT MINEDU v1.3.0

## 📋 PRE-REQUISITOS

### Sistema Base
- [ ] Docker >= 20.10.0 instalado
- [ ] Docker Compose >= 2.0.0 instalado  
- [ ] Python >= 3.8 instalado
- [ ] Git configurado
- [ ] Puertos libres: 8000, 3000, 9090, 9093, 9100

### Archivos del Proyecto
- [ ] `api_minedu.py` existe
- [ ] `requirements.txt` existe
- [ ] `docker-compose.production.yml` existe
- [ ] Directorio `src/core/` completo
- [ ] Directorio `data/` creado

## 🚀 PROCESO DE DEPLOYMENT

### Fase 1: Preparación (5 min)
```bash
# Verificar prerequisitos
./scripts/deploy-minedu.sh
```
- [ ] Repositorio actualizado
- [ ] Scripts tienen permisos de ejecución
- [ ] Prerequisitos verificados

### Fase 2: Instalación Dependencias (10 min)
```bash
# Instalar dependencias Python
pip install -r requirements.txt
pip install -r requirements.performance.txt
pip install -r requirements.monitoring.txt
```
- [ ] Dependencias base instaladas
- [ ] Dependencias de performance instaladas
- [ ] Dependencias de monitoring instaladas

### Fase 3: Configuración Vectorstores (15 min)
```bash
# Generar vectorstores si no existen
python src/data_pipeline/generate_vectorstores.py
```
- [ ] `data/vectorstores/bm25.pkl` existe
- [ ] `data/vectorstores/tfidf.pkl` existe  
- [ ] `data/vectorstores/transformers.pkl` existe

### Fase 4: Secrets Management (5 min)
```bash
# Crear secrets de Docker
chmod +x scripts/create-secrets.sh
./scripts/create-secrets.sh production
```
- [ ] Docker secrets creados
- [ ] SSL certificates generados

### Fase 5: Test Local (10 min)
```bash
# Probar API localmente
python api_minedu.py
curl http://localhost:8000/health
```
- [ ] API inicia sin errores
- [ ] Health check responde 200

### Fase 6: Deployment Docker (15 min)
```bash
# Deployment completo
docker-compose -f docker-compose.production.yml up -d
```
- [ ] Todos los containers "Up"
- [ ] API accesible en puerto 8000

### Fase 7: Monitoreo (10 min)
```bash
# Configurar monitoreo
./scripts/start-monitoring.sh production
```
- [ ] Prometheus corriendo en :9090
- [ ] Grafana corriendo en :3000

## 🧪 VALIDACIÓN FINAL

- [ ] API Backend: http://localhost:8000/health ✅
- [ ] Documentación: http://localhost:8000/docs ✅
- [ ] Métricas: http://localhost:8000/metrics ✅
- [ ] Grafana: http://localhost:3000 ✅
- [ ] Búsqueda híbrida funcional