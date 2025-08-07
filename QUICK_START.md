# 🚀 QUICK START - MINEDU v1.3.0

## ⚡ DEPLOYMENT EN 5 COMANDOS

```bash
# 1. Hacer scripts ejecutables
chmod +x scripts/*.sh

# 2. Deployment completo automatizado
./scripts/deploy-minedu.sh

# 3. Configurar monitoreo
./scripts/start-monitoring.sh production

# 4. Verificar que todo funciona
curl http://localhost:8000/health

# 5. Probar búsqueda
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "viáticos", "method": "hybrid"}'
```

## 📊 URLs IMPORTANTES

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| **API Backend** | http://localhost:8000 | - |
| **Documentación** | http://localhost:8000/docs | - |
| **Métricas** | http://localhost:8000/metrics | - |
| **Grafana** | http://localhost:3000 | admin/minedu_admin_2024 |
| **Prometheus** | http://localhost:9090 | - |

## 🔧 COMANDOS ÚTILES

```bash
# Ver logs en tiempo real
docker-compose -f docker-compose.production.yml logs -f

# Reiniciar servicios
docker-compose -f docker-compose.production.yml restart

# Parar todo
docker-compose -f docker-compose.production.yml down

# Ver métricas del sistema
curl http://localhost:8000/stats

# Test de búsqueda avanzada
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "¿Cuál es el monto máximo para viáticos de ministros?",
    "method": "hybrid",
    "top_k": 5
  }'
```

## 🆘 TROUBLESHOOTING RÁPIDO

**Error: Puerto ocupado**
```bash
sudo lsof -i :8000
sudo kill -9 <PID>
```

**Error: Vectorstores faltantes**
```bash
python src/data_pipeline/generate_vectorstores.py
```

**Error: Dependencies**
```bash
pip install -r requirements.txt --force-reinstall
```

---
**✅ Si todo funciona:** ¡Tu sistema MINEDU está listo para producción!