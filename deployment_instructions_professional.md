# 🚀 Deployment Instructions - LangGraph Professional System

## Sistema Completado - Características Implementadas

### ✅ LangGraph Real con StateGraph
- **Professional LangGraph** con 8 nodos especializados
- **Validación, retry y fallback** automáticos
- **Observabilidad completa** con trace IDs
- **Routing inteligente** por tipo de consulta

### ✅ Autenticación JWT Profesional
- **FastAPI Security** con roles (admin, user, demo)
- **Rate limiting** multinivel (30/min, 500/hora, 2000/día)
- **API keys** para acceso programático
- **Bcrypt hashing** para passwords

### ✅ Testing y Coverage
- **Coverage testing** con pytest y coverage.py
- **RAGAS evaluation** para métricas RAG
- **25+ tests profesionales** con AsyncMock
- **Baseline comparison** automático

### ✅ Containerización Docker
- **Multi-container** con backend, frontend, redis, nginx
- **Health checks** y restart policies
- **Monitoring opcional** con Prometheus/Grafana
- **Production-ready** configuration

### ✅ Streamlit UI Profesional
- **Autenticación integrada** con JWT
- **Observabilidad visual** con trace IDs
- **Testing interface** para coverage
- **RAGAS evaluation** en tiempo real

### ✅ Visualización LangGraph
- **Mermaid diagrams** del workflow
- **Graphviz generation** con colores
- **Execution traces** en HTML
- **Documentation** automática

## Quick Start - Deployment Profesional

### 1. Preparar el Entorno

```bash
# Clonar y navegar al proyecto
cd vm-expedientes-minedu

# Crear archivo de ambiente
cp .env.example .env

# Editar configuración para producción
nano .env
```

### 2. Docker Deployment (Recomendado)

```bash
# Build y start todos los servicios
docker-compose -f docker-compose.professional.yml up --build -d

# Verificar estado de servicios
docker-compose -f docker-compose.professional.yml ps

# Ver logs en tiempo real
docker-compose -f docker-compose.professional.yml logs -f backend
```

**Servicios disponibles:**
- **Backend API**: http://localhost:8000
- **Streamlit UI**: http://localhost:8501  
- **Redis**: localhost:6379
- **Nginx Proxy**: http://localhost

### 3. Manual Deployment

```bash
# Instalar dependencias
pip install -r requirements.txt
pip install -r backend/requirements.txt

# Instalar dependencias profesionales
pip install streamlit graphviz coverage pytest-asyncio ragas passlib[bcrypt]

# Ejecutar backend
cd backend/src
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# En otra terminal - Streamlit UI
streamlit run frontend/streamlit_professional.py --server.port 8501
```

## 🔐 Autenticación y Seguridad

### Usuarios Predefinidos

| Usuario | Password | Roles | Descripción |
|---------|----------|-------|-------------|
| admin | admin123 | admin, user | Administrador completo |
| consultor | consultor123 | user | Usuario consultor |
| demo | demo123 | demo | Usuario demo limitado |

### API Keys de Desarrollo

```bash
# Headers para requests
Authorization: Bearer mk_dev_admin_2025    # Usuario admin
Authorization: Bearer mk_dev_user_2025     # Usuario consultor  
Authorization: Bearer mk_demo_2025         # Usuario demo
```

### Cambiar en Producción

```bash
# Generar secret key segura
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Actualizar en .env
JWT_SECRET_KEY=tu_secret_key_aqui

# Cambiar passwords por defecto
# Editar backend/src/core/auth/jwt_auth.py líneas 57-81
```

## 📊 Testing y Quality Assurance

### Ejecutar Tests Completos

```bash
# Tests con coverage
python backend/src/core/testing/coverage_config.py

# O usar make si está configurado
make test

# Solo tests profesionales de LangGraph
pytest backend/tests/test_professional_langgraph.py -v
```

### RAGAS Evaluation

```bash
# Evaluación manual
python backend/src/core/evaluation/ragas_evaluator.py

# O desde Streamlit UI tab "Evaluación RAGAS"
```

### Visualización del Workflow

```bash
# Generar diagramas
python backend/src/core/visualization/langgraph_visualizer.py

# Archivos generados en visualization_output/
# - workflow_mermaid.md
# - langgraph_workflow_TIMESTAMP.png 
# - workflow_documentation.md
# - execution_trace_TIMESTAMP.html
```

## 🎯 Uso del Sistema

### 1. API Endpoints

```bash
# Autenticación
POST /auth/login
POST /auth/refresh

# Consultas RAG
POST /api/chat/professional    # LangGraph profesional (recomendado)
POST /api/chat/real           # LangGraph básico
POST /api/chat/hybrid         # Sistema híbrido legacy

# Estado y monitoreo
GET /status
GET /health

# Testing y evaluación
POST /testing/coverage
POST /evaluation/ragas
```

### 2. Streamlit UI

**Acceder a:** http://localhost:8501

1. **Autenticarse** con credenciales
2. **Tab "Consultas RAG"**: Interfaz principal
   - Seleccionar método (professional recomendado)
   - Ingresar consulta
   - Ver respuesta con trace ID y métricas
3. **Tab "Estado del Sistema"**: Monitoreo en tiempo real
4. **Tab "Testing"**: Ejecutar coverage tests
5. **Tab "Evaluación RAGAS"**: Evaluar calidad de respuestas
6. **Tab "Visualización"**: Diagramas del workflow

### 3. Consultas de Ejemplo

```json
// Consulta de viáticos
{
  "query": "¿Cuál es el monto máximo de viáticos en provincias?"
}

// Respuesta esperada
{
  "response": "El monto máximo para viáticos en provincias es S/ 320.00 soles por día, según la Directiva N° 011-2020-MINEDU.",
  "method": "professional_langgraph", 
  "confidence": 0.92,
  "documents_found": 3,
  "processing_time": 1.85,
  "extracted_info": {
    "trace_id": "trace_1704123456789",
    "selected_agent": "viaticos",
    "used_fallback": false,
    "validation_errors": []
  }
}
```

## 🔧 Configuración Avanzada

### Variables de Entorno

```bash
# Seguridad
JWT_SECRET_KEY=tu_secret_key_production
JWT_EXPIRATION_HOURS=24

# Base de datos (futuro)
DATABASE_URL=postgresql://user:pass@localhost/minedu_rag

# Redis
REDIS_URL=redis://localhost:6379

# LLM
OPENAI_API_KEY=tu_openai_key
ANTHROPIC_API_KEY=tu_anthropic_key

# Monitoring
ENABLE_PROMETHEUS=true
GRAFANA_ADMIN_PASSWORD=tu_password_seguro
```

### Nginx Configuration

```nginx
# Actualizar nginx.professional.conf para producción
server_name tu-dominio.com;

# Agregar SSL
listen 443 ssl;
ssl_certificate /path/to/cert.pem;
ssl_certificate_key /path/to/key.pem;
```

### Monitoring con Prometheus

```bash
# Iniciar con monitoring
docker-compose -f docker-compose.professional.yml --profile monitoring up -d

# Acceder a:
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/minedu2025)
```

## 📈 Métricas y Observabilidad

### Métricas Clave

- **Tiempo de respuesta promedio**: < 2 segundos
- **Tasa de éxito**: > 90% sin fallback
- **Coverage de tests**: > 80%
- **Score RAGAS promedio**: > 0.8

### Trace Information

Cada consulta genera:
- **Trace ID único**: Para debugging
- **Node history**: Nodos ejecutados
- **Processing time**: Tiempo total
- **Agent information**: Agente usado y intentos
- **Validation status**: Errores de validación

### Logs Estructurados

```json
{
  "timestamp": "2025-01-02T15:30:45Z",
  "level": "INFO", 
  "trace_id": "trace_1704123456789",
  "node": "execute_agent",
  "agent": "viaticos",
  "query": "monto de viáticos",
  "processing_time": 1.85,
  "confidence": 0.92
}
```

## 🚨 Troubleshooting

### Problemas Comunes

1. **LangGraph no se carga**
   ```bash
   # Verificar instalación
   pip install langgraph langchain langchain-community
   
   # Verificar imports
   python -c "from langgraph.graph import StateGraph; print('OK')"
   ```

2. **JWT Authentication falla**
   ```bash
   # Verificar secret key
   echo $JWT_SECRET_KEY
   
   # Regenerar token
   curl -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin123"}'
   ```

3. **Docker containers no inician**
   ```bash
   # Ver logs detallados
   docker-compose -f docker-compose.professional.yml logs backend
   
   # Rebuild containers
   docker-compose -f docker-compose.professional.yml down
   docker-compose -f docker-compose.professional.yml up --build
   ```

4. **Coverage tests fallan**
   ```bash
   # Verificar pytest
   cd backend && python -m pytest --version
   
   # Ejecutar tests individuales
   pytest backend/tests/test_professional_langgraph.py::TestProfessionalLangGraph::test_input_validation_valid_query -v
   ```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Sistema status
curl -H "Authorization: Bearer tu_token" http://localhost:8000/status

# Docker health
docker-compose -f docker-compose.professional.yml ps
```

## 📝 Próximos Pasos

### Optimizaciones Recomendadas

1. **Base de datos real** (PostgreSQL)
2. **Vector database** (Pinecone/Chroma)  
3. **Caching avanzado** (Redis Cluster)
4. **Load balancing** (múltiples instancias)
5. **CI/CD pipeline** (GitHub Actions)

### Monitoreo Avanzado

1. **APM** (Application Performance Monitoring)
2. **Error tracking** (Sentry)
3. **Log aggregation** (ELK Stack)
4. **Alerting** (PagerDuty/Slack)

---

## 🎉 ¡Sistema Profesional Completado!

El sistema MINEDU RAG ahora cuenta con:

✅ **LangGraph Real** con StateGraph profesional  
✅ **JWT Authentication** con roles y permisos  
✅ **Coverage Testing** con pytest y RAGAS  
✅ **Docker Deployment** production-ready  
✅ **Streamlit UI** con observabilidad completa  
✅ **Workflow Visualization** con Mermaid/Graphviz  

**Tu sistema está listo para producción.** 🚀

Para soporte adicional, consultar:
- 📚 `workflow_documentation.md` generado
- 🔍 Logs en `docker-compose logs`
- 📊 Métricas en Streamlit UI
- 🎯 Tests en `backend/tests/`