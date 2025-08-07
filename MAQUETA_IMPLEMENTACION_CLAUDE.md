# 🎯 MAQUETA DE IMPLEMENTACIÓN - VM-EXPEDIENTES-MINEDU

**IMPORTANTE PARA CLAUDE CODE**: Este documento es mi guía maestra de implementación. 
Contiene la ingeniería de contexto y el roadmap completo del proyecto. Lo uso como 
referencia constante para mantener coherencia y evitar alucinaciones.

## 📌 INSTRUCCIÓN PRINCIPAL
Soy el ingeniero principal del sistema RAG normativo MINEDU. Este documento define:
1. Mi protocolo de trabajo (ingeniería de contexto)
2. Las 7 fases del proyecto (roadmap)
3. El estado actual y próximos pasos

**REGLA DE ORO**: Nunca implemento algo que no esté verificado contra este documento.

---

## 🔧 PARTE 1: INGENIERÍA DE CONTEXTO

### 🚨 PROTOCOLO ANTIALUCINACIONES

#### **NIVEL 1: VERIFICACIÓN FÍSICA**
- ✅ **SIEMPRE verificar con comandos** antes de reportar
- ✅ **Contrastar con CONTEXTO_CLAUDE_PERSISTENTE.md** 
- ✅ **Usar test_cordura.py** para validar funcionalidad
- ❌ **NUNCA reportar sin evidencia física**

#### **NIVEL 2: CONFIANZA Y TRANSPARENCIA**
```
[CONFIANZA 85% | VERIFICADO EN /backend/src/main.py:1352 | RIESGOS: LangChain faltante]
```
- **Confianza < 75%** → Solicitar aclaración
- **Dato faltante** → Usar TODO_CRITICAL o TODO_MINOR
- **Circuit breaker activo** → DETENER y reportar

#### **NIVEL 3: REFERENCIAS PRECISAS**
- **Archivos**: `file_path:line_number` formato obligatorio
- **Estados**: Solo desde verificación real, no asunciones
- **Métricas**: Solo medidas, no estimadas

---

## 🗺️ PARTE 2: ROADMAP DE 7 FASES

### **MATRIZ DE CAPACIDADES POR FASE**

| Capacidad | F1 | F2 | F3 | F4 | F5 | F6 | F7 |
|-----------|----|----|----|----|----|----|----| 
| RAG básico | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Razonamiento | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Multiagente | ❌ | ❌ | 🔄 | ✅ | ✅ | ✅ | ✅ |
| Investigación | ❌ | ❌ | 🔄 | 🔄 | ✅ | ✅ | ✅ |
| Interoperabilidad | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Auditoría autónoma | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Plataforma cognitiva | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

### **FASES DETALLADAS**

#### **FASE 1: Fundacional Operativa** ✅ COMPLETADA
- **Objetivo**: RAG funcional sin costo
- **Estado verificado**: Backend 8001 + Frontend 3000 operativos
- **Evidencia**: `curl http://localhost:8001/health` → {"status":"healthy"}

#### **FASE 2: RAGOS (RAG OSS Escalado)** ✅ COMPLETADA  
- **Objetivo**: Múltiples algoritmos búsqueda
- **Estado verificado**: BM25, TF-IDF, SimpleRetriever funcionando
- **Evidencia**: `test_cordura.py` → 5 documentos encontrados

#### **FASE 3: Inteligencia Legal Real** 🚧 EN PROGRESO
- **Objetivo**: Razonamiento legal verdadero sobre normativas
- **Estado verificado**: Motor legal implementado, RAG profesional funcionando
- **Evidencia**: `backend/src/domain/legal_reasoning.py:137` líneas
- **Pendiente**: Integrar razonamiento en todas las respuestas

#### **FASE 4: Interoperabilidad Institucional** ⏳ PENDIENTE
- **Objetivo**: Conexión sistemas gubernamentales + Supabase
- **Dependencias**: Fase 3 completada
- **Costo estimado**: $0-25/mes Supabase

#### **FASE 5: IA Legal Multiagente** ⏳ PENDIENTE
- **Objetivo**: Agentes especializados por área legal
- **Arquitectura**: Tributario + Constitucional + Administrativo
- **Dependencias**: Fase 4 base de datos

#### **FASE 6: Auditoría Inteligente Autónoma** ⏳ PENDIENTE
- **Objetivo**: Sistema observador detectando inconsistencias
- **Dependencias**: Fase 5 multiagente

#### **FASE 7: Plataforma Cognitiva Legal** ⏳ PENDIENTE
- **Objetivo**: Sistema cognitivo completo sector público
- **Dependencias**: Todas las fases anteriores

---

## 🎯 PARTE 3: RESPUESTA A CONSULTAS ESPECÍFICAS

### **INVESTIGACIONES TRIBUTARIAS CON RAZONAMIENTO**

#### **Ejemplo de investigación tributaria deseada:**
```
Consulta: "¿Una empresa que vende software puede acogerse al drawback si exporta servicios digitales?"

Respuesta esperada (Fase 7):
- Análisis del régimen drawback (norma aduanera)
- Concordancia con definición de exportación de servicios (IGV)
- Verificación constitucional (principio de igualdad tributaria)  
- Jurisprudencia del Tribunal Fiscal
- Conclusión fundamentada con citas específicas
```

#### **Arquitectura de razonamiento:**
```
Usuario → Orquestador → [Agente Tributario + Agente Constitucional + Agente Administrativo]
    ↓
Consolidación y concordancia
    ↓
Respuesta fundamentada con trazabilidad
```

#### **Implementación por fases:**
- **Fase 3**: Razonamiento básico en cada agente
- **Fase 5**: Agentes especializados (tributario, constitucional, administrativo)
- **Fase 7**: Integración completa con concordancia entre todas las normas

---

## ⚡ ESTADO ACTUAL VERIFICADO (2025-07-04 15:02 UTC)

### **VERIFICACIONES FÍSICAS REALIZADAS:**
```bash
# Backend funcionando
curl http://localhost:8001/health
# Result: {"status":"healthy","version":"2.0.0"}

# RAG profesional funcionando
curl -X POST http://localhost:8001/api/chat/professional -d '{"message":"monto viáticos"}'
# Result: "SISTEMA PROFESIONAL RAG MINEDU" + 5 documentos encontrados

# SimpleRetriever cargado
backend/src/langchain_integration/vectorstores/simple_retriever.py:222
# Result: 12 documentos cargados desde chunks.json

# Motor legal implementado
backend/src/domain/legal_reasoning.py:137
# Result: LegalReasoner class completa
```

### **CONFIANZA ACTUAL**: 95%
- ✅ **RAG real funcionando**: Datos extraídos de chunks físicos
- ✅ **SimpleRetriever operativo**: 12 documentos, 5 encontrados por consulta
- ✅ **Motor legal implementado**: 137 líneas de código verificadas
- ⚠️ **LangGraph pendiente**: Dependencias no instaladas (parche activo)

### **PRÓXIMOS PASOS VERIFICADOS:**
1. **Completar Fase 3**: Integrar motor legal en todas las respuestas
2. **Instalar LangChain** (opcional): Para funcionalidad completa
3. **Preparar Fase 4**: Definir integración Supabase

---

## 🚨 RECORDATORIOS CRÍTICOS

### **ANTES DE CADA RESPUESTA VERIFICAR:**
- [ ] **Estado físico**: ¿Los servicios están corriendo?
- [ ] **Contexto actualizado**: ¿Coincide con CONTEXTO_CLAUDE_PERSISTENTE.md?
- [ ] **Referencias exactas**: ¿Tengo file_path:line_number?
- [ ] **Confianza medida**: ¿> 75%?

### **FORMATO OBLIGATORIO DE RESPUESTA:**
```
[CONFIANZA X% | SNAPSHOT Xh | RIESGOS: Y]

Respuesta técnica con referencias exactas...

backend/src/main.py:1352 - Endpoint profesional
```

### **CIRCUIT BREAKERS:**
- **Si confianza < 75%** → "Necesito verificar X antes de continuar"
- **Si falta archivo** → "El archivo X no existe, verificando alternativas"
- **Si discrepancia** → "Detecto inconsistencia entre X e Y, investigando"

---

## 📊 MÉTRICAS DE CALIDAD

### **ANTI-ALUCINACIÓN SCORE**
- **Verificaciones físicas**: 100% obligatorias
- **Referencias precisas**: formato file_path:line_number
- **Transparencia**: Confianza + Riesgos siempre explícitos
- **Coherencia**: Contrastar con documentos maestros

### **ÚLTIMA VERIFICACIÓN**: 2025-07-04 15:02 UTC
### **PRÓXIMA VERIFICACIÓN**: Antes de cada cambio significativo

---

**NOTA FINAL**: Este documento es mi protocolo de trabajo. No implemento nada sin verificar contra esta maqueta.