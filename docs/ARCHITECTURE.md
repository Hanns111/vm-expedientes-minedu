# ARQUITECTURA DEL SISTEMA RAG MINEDU v1.4.0

## 🏗️ VISIÓN GENERAL

Sistema RAG híbrido empresarial para el Ministerio de Educación del Perú, desarrollado con LangGraph profesional, autenticación empresarial, y capacidades avanzadas de reranking y feedback continuo.

## 📊 ARQUITECTURA DE ALTO NIVEL

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│  • Streamlit Professional UI                                   │
│  • Next.js React Application                                   │
│  • JWT Authentication + OAuth2                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      API LAYER                                 │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI Application                                           │
│  ├─ /api/chat/professional  (LangGraph Main Endpoint)          │
│  ├─ /api/feedback/*         (User Feedback System)            │
│  ├─ /api/reranker/*         (Advanced Reranking)              │
│  ├─ /api/calculations/*     (Normative Calculations)          │
│  └─ /api/auth/*             (JWT + OAuth2)                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   ORCHESTRATION LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│  LangGraph Professional StateGraph                             │
│  ├─ input_validation     → detect_intent                       │
│  ├─ route_to_agent      → execute_agent (+ reranking)         │
│  ├─ validate_response   → fallback_legacy                      │
│  └─ compose_response    → END                                  │
│                                                                │
│  Features:                                                     │
│  • Real StateGraph (no simulator)                             │
│  • MemorySaver + CompiledGraph                                │
│  • Validation, Retry, Fallback                                │
│  • Complete Observability                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    INTELLIGENCE LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│  Specialized Agents:                                           │
│  ├─ ViaticosAgent        (Travel allowances specialist)        │
│  ├─ DetraccionsAgent     (Tax deductions - future)            │
│  ├─ AuditAgent          (Audit procedures - future)           │
│  └─ LegalAgent          (Legal verification - future)         │
│                                                                │
│  Advanced Reranker:                                            │
│  ├─ Cross-Encoder (ms-marco-MiniLM-L-6-v2)                   │
│  ├─ Hybrid Strategies                                         │
│  ├─ MINEDU-specific term boosting                            │
│  └─ Fallback heuristics                                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    RETRIEVAL LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│  Hybrid Search System:                                         │
│  ├─ BM25Retriever        (Lexical search, Spanish-optimized)   │
│  ├─ TFIDFRetriever       (Vectorial search)                   │
│  └─ TransformerRetriever (Semantic search, multilingual-e5)   │
│                                                                │
│  Fusion Strategies:                                            │
│  ├─ Weighted Fusion                                           │
│  ├─ Reciprocal Rank Fusion (RRF)                             │
│  └─ Amount-aware boosting                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     COMPUTATION LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│  Normative Calculator (pandas/numpy):                          │
│  ├─ UIT values (historical)                                   │
│  ├─ Exchange rates (USD/PEN)                                  │
│  ├─ Travel allowances by year/level                           │
│  └─ Sanctions and infractions                                 │
│                                                                │
│  Temporal Legal Processor:                                     │
│  ├─ Year detection in queries                                 │
│  ├─ Historical regulation mapping                             │
│  ├─ Temporal context enhancement                              │
│  └─ Comparative analysis                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL Database:                                          │
│  ├─ Users (authentication, roles)                             │
│  ├─ QueryLogs (system performance)                            │
│  ├─ SystemMetrics (feedback, analytics)                       │
│  └─ AuditLogs (security compliance)                           │
│                                                                │
│  Vectorstores:                                                │
│  ├─ bm25.pkl            (BM25 index)                         │
│  ├─ tfidf.pkl           (TF-IDF vectors)                     │
│  └─ transformers.pkl    (Dense embeddings)                   │
│                                                                │
│  Document Sources:                                             │
│  ├─ MINEDU Directives (PDF)                                  │
│  ├─ Legal Decrees                                            │
│  └─ Administrative Procedures                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     SECURITY LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  Authentication & Authorization:                               │
│  ├─ JWT tokens with role-based access                         │
│  ├─ OAuth2 (Google/Microsoft) with PKCE                      │
│  ├─ Password hashing (bcrypt)                                 │
│  └─ Session management                                        │
│                                                                │
│  Input Protection:                                             │
│  ├─ Query sanitization                                        │
│  ├─ SQL/NoSQL injection prevention                           │
│  ├─ LLM prompt injection protection                          │
│  └─ XSS prevention                                           │
│                                                                │
│  Operational Security:                                         │
│  ├─ Rate limiting (30/min, 500/hour, 2000/day)              │
│  ├─ PII detection and anonymization                          │
│  ├─ Comprehensive audit logging                              │
│  ├─ File validation and safe pickle loading                  │
│  └─ Secrets management                                       │
│                                                                │
│  Compliance:                                                  │
│  ├─ ISO27001 alignment                                       │
│  ├─ NIST Cybersecurity Framework                             │
│  └─ Government data protection standards                      │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 FLUJO DE PROCESAMIENTO

### 1. Request Flow
```
User Query → JWT Validation → Input Sanitization → LangGraph Professional
```

### 2. LangGraph Professional Flow
```
input_validation → detect_intent → route_to_agent → execute_agent → 
(Advanced Reranking) → validate_response → (fallback_legacy) → 
compose_response → Response
```

### 3. Advanced Reranking Flow (Inside execute_agent)
```
Agent Results → Document Preparation → Cross-Encoder/Hybrid Strategy → 
Reranked Results → Confidence Update → Continue LangGraph
```

### 4. Feedback Loop
```
User Response → User Rating → PostgreSQL → Analytics → Quality Insights → 
System Optimization Recommendations
```

## 🎯 COMPONENTES CLAVE

### LangGraph Professional StateGraph
- **Real StateGraph**: No simulador, implementación completa
- **MemorySaver**: Checkpointing para conversaciones
- **CompiledGraph**: Optimización de performance
- **8 Nodos Especializados**: Cada uno con función específica
- **Conditional Edges**: Lógica de retry y fallback
- **Complete Observability**: Trace IDs, node history, metrics

### Advanced Reranker System
- **Cross-Encoder**: Neural reranking con ms-marco-MiniLM-L-6-v2
- **Hybrid Strategies**: Cross-encoder → semantic → fallback
- **MINEDU Domain Knowledge**: Term boosting específico
- **Performance Metrics**: Processing time, strategy usage stats
- **Async Processing**: No bloquea el flujo principal

### Feedback & Analytics System
- **User Ratings**: 1-5 stars con categorización
- **Quality Analytics**: Confidence calibration, method performance
- **Trend Analysis**: Monthly trends, improvement recommendations
- **Continuous Improvement**: Data-driven system optimization

### Normative Calculator
- **Pandas/Numpy**: Cálculos científicos estándar
- **Historical Data**: UIT, exchange rates, allowances by year
- **Temporal Queries**: Aplicación de normativa histórica
- **Comparative Analysis**: Year-over-year changes

### Security & Compliance
- **Government-Grade**: ISO27001, NIST compliance
- **Multi-Layer Protection**: Authentication, input validation, monitoring
- **Audit Trail**: Complete logging for transparency
- **Role-Based Access**: Admin, user, demo roles

## 📊 INTEGRACIONES

### Database Integration
```python
# Repository Pattern with Unit of Work
async with UnitOfWork(session) as uow:
    user = await uow.users.get_by_id(user_id)
    await uow.metrics.record_metric(feedback_data)
    await uow.audit.log_action(action_data)
    await uow.commit()
```

### LangGraph Integration
```python
# Professional orchestrator with reranking
final_state = await self.compiled_graph.ainvoke(
    initial_state,
    config={"configurable": {"thread_id": thread_id}}
)
```

### Advanced Reranker Integration
```python
# Integrated in execute_agent node
reranked_results = await rerank_search_results(
    query=state["query"],
    documents=documents_for_rerank,
    strategy="hybrid"
)
```

## 🔧 CONFIGURACIÓN Y DEPLOYMENT

### Environment Variables
```env
# Database
DATABASE_URL=postgresql://...
REDIS_URL=redis://...

# Authentication
JWT_SECRET_KEY=...
GOOGLE_CLIENT_ID=...
MICROSOFT_CLIENT_ID=...

# AI Models
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...

# Security
RATE_LIMIT_ENABLED=true
AUDIT_LOGGING_ENABLED=true
```

### Docker Composition
```yaml
services:
  backend:
    build: ./backend
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=minedu_rag
      - POSTGRES_USER=minedu_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
```

## 📈 OBSERVABILIDAD Y MONITOREO

### Metrics Collection
- **Response Times**: Latencia por componente
- **User Satisfaction**: Ratings y feedback analysis
- **System Performance**: Memory, CPU, DB query times  
- **Security Events**: Failed authentication, suspicious patterns
- **Business Metrics**: Query types, agent usage, confidence scores

### Logging Levels
- **INFO**: Normal operations, user actions
- **WARNING**: Fallback usage, low confidence responses
- **ERROR**: System errors, failed operations
- **AUDIT**: Security events, data access, admin actions

### Health Checks
```python
# Built-in health endpoints
GET /health              # Basic system health
GET /health/database     # Database connectivity
GET /health/vectorstores # Vectorstore availability
GET /health/auth         # Authentication services
```

## 🚀 ESCALABILIDAD

### Horizontal Scaling
- **Stateless Design**: Cada request independiente
- **Load Balancing**: Multiple backend instances
- **Database Sharding**: User-based partitioning
- **Caching Strategy**: Redis para session data, query results

### Performance Optimization
- **Async Processing**: FastAPI + asyncio
- **Connection Pooling**: PostgreSQL, Redis
- **Vectorstore Caching**: In-memory loading
- **Lazy Loading**: Models cargados on-demand

### Multi-Agent Scaling
```python
# Extensible agent architecture
self.agents = {
    "viaticos": ViaticosAgent(),
    "detracciones": DetraccionesAgent(),  # Future
    "auditoria": AuditoriaAgent(),        # Future
    "legal": LegalAgent(),                # Future
}
```

## 🎯 PRINCIPIOS DE DISEÑO

1. **Security First**: Seguridad gubernamental en cada capa
2. **Observability**: Trazabilidad completa de operaciones
3. **Reliability**: Fallbacks y retry logic robusto
4. **Scalability**: Arquitectura preparada para crecimiento
5. **Maintainability**: Código modular y bien documentado
6. **Performance**: Optimización en cada componente crítico
7. **Compliance**: Cumplimiento normativo y auditoría

---
*Arquitectura Sistema RAG MINEDU v1.4.0*
*Enterprise-grade system for Peru Ministry of Education*