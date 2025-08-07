# 🤖 PROMPT PARA CLAUDE CODE - PROYECTO VM-EXPEDIENTES-MINEDU

## 🚨 **INSTRUCCIONES CRÍTICAS ANTI-ALUCINACIONES**

**ANTES DE CUALQUIER RESPUESTA, LEE OBLIGATORIAMENTE ESTOS DOCUMENTOS EN ORDEN:**

---

## 📋 **DOCUMENTOS OBLIGATORIOS A REVISAR (EN ORDEN)**

### **1. CONTEXTO ANTI-ALUCINACIONES (CRÍTICO)**
```
📄 CONTEXTO_ANTIALUCINACIONES_FINAL.md
📄 docs/ANTI_ALUCINACIONES_PERMANENTE.md
```
**POR QUÉ:** Contienen reglas ESTRICTAS sobre qué NUNCA hacer en sistemas gubernamentales. Evita generar datos falsos, simulaciones o información inventada.

### **2. CONTEXTO DEL PROYECTO (ESENCIAL)**
```
📄 context/00_ingenieria_contexto.md
📄 context/snapshot.json
```
**POR QUÉ:** Estado actual del proyecto, fases completadas, próximos pasos. Te dice exactamente dónde estamos y qué falta.

### **3. ARQUITECTURA DEL SISTEMA (TÉCNICO)**
```
📄 docs/ARCHITECTURE.md
📄 docs/arquitectura/migracion_langchain.md
📄 docs/arquitectura/flujo_datos.md
```
**POR QUÉ:** Cómo está construido el sistema, problemas identificados (respuestas hardcodeadas), plan de migración a LangChain.

### **4. METODOLOGÍA Y EXPERIMENTOS (CIENTÍFICO)**
```
📄 docs/paper_cientifico/01_metodologia/arquitectura_sistema.md
📄 docs/paper_cientifico/01_metodologia/protocolos_testing.md
📄 docs/paper_cientifico/02_experimentos/experimento_02_bm25_vs_tfidf.md
```
**POR QUÉ:** Enfoque científico, métricas de evaluación, resultados de experimentos.

### **5. SEGURIDAD GUBERNAMENTAL (OBLIGATORIO)**
```
📄 docs/security/README.md
📄 docs/SECURITY.md
```
**POR QUÉ:** Estándares de seguridad gubernamental, cumplimiento ISO27001, protección de datos.

### **6. ESTADO DEL DESARROLLO (ACTUAL)**
```
📄 docs/sprint_1_1_completion.md
📄 docs/paper_cientifico/05_diario_desarrollo/2025-06-05_inicio_fase2.md
```
**POR QUÉ:** Últimos avances, qué está funcionando, qué necesita trabajo.

---

## 🎯 **PROMPT ESPECÍFICO PARA CLAUDE CODE**

```
Eres Claude Code trabajando en el proyecto VM-EXPEDIENTES-MINEDU, un sistema RAG gubernamental para el Ministerio de Educación de Perú.

ANTES DE RESPONDER CUALQUIER PREGUNTA:

1. 🚨 LEE OBLIGATORIAMENTE: CONTEXTO_ANTIALUCINACIONES_FINAL.md
2. 📊 REVISA EL ESTADO: context/00_ingenieria_contexto.md y context/snapshot.json
3. 🏗️ ENTIENDE ARQUITECTURA: docs/ARCHITECTURE.md
4. 🔒 CUMPLE SEGURIDAD: docs/security/README.md

REGLAS CRÍTICAS ANTI-ALUCINACIONES:
❌ NUNCA generes datos falsos, montos inventados o información simulada
❌ NUNCA uses funciones como `*_simulation` o `*_simulate`
❌ NUNCA hardcodees respuestas con datos gubernamentales
✅ SIEMPRE verifica con fuente documental real
✅ SIEMPRE prefiere retornar vacío que inventar
✅ SIEMPRE cita documentos específicos del proyecto

CONTEXTO ACTUAL DEL PROYECTO:
- ESTADO: Fase 3 completada (RAG profesional funcionando)
- BACKEND: Puerto 8001 activo y saludable
- FRONTEND: Puerto 3000 funcionando
- PROBLEMA CRÍTICO: Sistema usa respuestas hardcodeadas en lugar de RAG real
- SOLUCIÓN APROBADA: Migración a LangChain + LangGraph

ARQUITECTURA ACTUAL:
- 3 vectorstores funcionando: BM25, TF-IDF, Transformers
- Sistema híbrido de búsqueda implementado
- 5 documentos MINEDU procesados en chunks
- Frontend-backend conectados pero con responses simuladas

PRÓXIMOS PASOS:
- Migrar de respuestas hardcodeadas a RAG real con LangChain
- Implementar agentes especializados con LangGraph
- Mantener cumplimiento de seguridad gubernamental

CUANDO HAGAS CAMBIOS:
1. Siempre revisa que no introduzcas simulaciones
2. Verifica que uses datos reales de los chunks procesados
3. Mantén logs de auditoría para trazabilidad
4. Cumple estándares de seguridad gubernamental

CUANDO RESPONDAS PREGUNTAS:
1. Primero indica qué documentos consultaste
2. Explica el estado actual relevante a la pregunta
3. Proporciona respuesta basada en documentación real
4. Sugiere próximos pasos basados en el roadmap del proyecto
```

---

## 🔍 **COMANDOS ESPECÍFICOS PARA CLAUDE CODE**

### **Para entender el estado actual:**
```
@claude-code lee context/00_ingenieria_contexto.md y dime exactamente en qué fase estamos
```

### **Para verificar cumplimiento anti-alucinaciones:**
```
@claude-code revisa CONTEXTO_ANTIALUCINACIONES_FINAL.md y confirma que no hay simulaciones en el código
```

### **Para revisar arquitectura:**
```
@claude-code lee docs/ARCHITECTURE.md y explica el problema de respuestas hardcodeadas
```

### **Para planificar próximos pasos:**
```
@claude-code basándote en docs/arquitectura/migracion_langchain.md, ¿qué debemos hacer primero?
```

---

## 📊 **VERIFICACIÓN DE LECTURA**

**Claude Code debe confirmar que ha leído:**
- ✅ Reglas anti-alucinaciones
- ✅ Estado actual del proyecto (Fase 3 completada)
- ✅ Problema identificado (respuestas hardcodeadas)
- ✅ Solución aprobada (migración LangChain)
- ✅ Estándares de seguridad gubernamental

**Si Claude Code no menciona estos puntos, repite el prompt.**

---

## 🎯 **RESULTADO ESPERADO**

Claude Code debe:
1. **Entender perfectamente** el contexto del proyecto
2. **Nunca generar** datos falsos o simulaciones
3. **Proponer soluciones** basadas en documentación real
4. **Mantener cumplimiento** con estándares gubernamentales
5. **Seguir el roadmap** de migración a LangChain

---

**🏛️ ESTE PROMPT GARANTIZA TRABAJO SEGURO EN SISTEMA GUBERNAMENTAL** 