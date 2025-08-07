# 🤖 PROTOCOLO DE TRABAJO: CLAUDE + CURSOR

## 📋 **DIVISIÓN DE TAREAS ESTRATÉGICA**

### 🧠 **TAREAS PARA CLAUDE (IA)**
✅ **Diseño y Arquitectura**
- Planificación de componentes y APIs
- Diseño de patrones y estructuras de datos
- Definición de interfaces y contratos
- Revisión y validación de código

✅ **Lógica Compleja** 
- Algoritmos de búsqueda y ranking
- Procesamiento de lenguaje natural
- Análisis semántico y concordancia
- Métricas y evaluación

✅ **Integración y Orquestación**
- Conexión entre componentes
- Flujos de datos complejos
- Manejo de estados y errores
- Documentación técnica

### 🖥️ **TAREAS PARA CURSOR (HUMANO + IDE)**
✅ **Ejecución y Testing**
- Instalación de dependencias
- Ejecución de comandos y scripts
- Testing y debugging
- Verificación de imports

✅ **Operaciones de Sistema**
- Manipulación de archivos
- Configuración de entorno
- Git operations
- Builds y deployments

✅ **Tareas Repetitivas**
- Creación de archivos básicos/boilerplate
- Formateo y linting
- Copiar/pegar código estructurado
- Verificación de sintaxis

## 🔄 **PROTOCOLO DE TRABAJO**

### **FLUJO ESTÁNDAR:**

1. **Claude analiza** la tarea y determina división
2. **Claude proporciona** instrucciones específicas para Cursor
3. **Usuario ejecuta** en Cursor las instrucciones
4. **Usuario reporta** resultados completos a Claude
5. **Claude valida** y proporciona siguiente paso

### **FORMATO DE INSTRUCCIONES CLAUDE → CURSOR:**

```markdown
## 🖥️ INSTRUCCIONES PARA CURSOR:

### **TAREA:** [Descripción breve]

#### **1. Comando/Acción:**
```bash
[comando específico]
```

#### **2. Crear archivo:** `ruta/archivo.py`
```python
[código completo]
```

#### **3. Verificar resultado:**
```bash
[comando de verificación]
```

### **REPORTAR A CLAUDE:**
- Copia TODA la salida de cada comando
- Incluye cualquier error o warning
- Confirma éxito/fallo de cada paso
```

### **FORMATO DE REPORTE CURSOR → CLAUDE:**

```markdown
## 📊 REPORTE DE EJECUCIÓN:

### **Paso 1 - [Descripción]:**
✅/❌ Estado: [Éxito/Error]
```
[Salida completa del comando]
```

### **Paso 2 - [Descripción]:**
✅/❌ Estado: [Éxito/Error]
```
[Salida completa del comando]
```

### **RESUMEN:**
- Total pasos ejecutados: X
- Exitosos: X
- Con errores: X
- Observaciones: [Cualquier nota relevante]
```

## 🎯 **BENEFICIOS DE ESTE PROTOCOLO:**

✅ **Eficiencia de tokens** - Cursor hace operaciones simples
✅ **Calidad asegurada** - Claude revisa todo
✅ **Velocidad óptima** - Tareas paralelas
✅ **Control de calidad** - Validación constante
✅ **Comunicación clara** - Formato estandarizado

## 🚨 **REGLAS IMPORTANTES:**

### **PARA CLAUDE:**
- SIEMPRE proporcionar instrucciones específicas y completas
- NUNCA asumir que algo funcionó sin confirmación
- SIEMPRE validar respuestas de Cursor antes de continuar
- Proporcionar código completo, no fragmentos

### **PARA CURSOR/USUARIO:**
- EJECUTAR exactamente las instrucciones proporcionadas
- REPORTAR toda la salida, incluso si parece trivial
- NO modificar comandos sin consultar
- CONFIRMAR cada paso antes del siguiente

## 🔧 **COMANDOS DE VERIFICACIÓN ESTÁNDAR:**

### **Python/Imports:**
```bash
python -c "
import sys
sys.path.append('.')
try:
    from [módulo] import [clase]
    print('✅ [Nombre]: OK')
except Exception as e:
    print(f'❌ [Nombre]: {e}')
"
```

### **Estructura de archivos:**
```bash
find . -name "*.py" -path "./src/*" | head -20
```

### **Testing básico:**
```bash
python -m pytest [archivo_test] -v
```

### **Demo/Aplicación:**
```bash
python [archivo_demo].py
```

## 📁 **ESTE ARCHIVO:**

- **Ubicación:** `/PROTOCOLO_TRABAJO_CLAUDE_CURSOR.md`
- **Propósito:** Referencia permanente para coordinación eficiente
- **Actualización:** Solo cuando se mejore el protocolo
- **Uso:** Claude lo consulta antes de dar instrucciones

---

**VERSIÓN:** 1.0  
**FECHA:** $(date +'%Y-%m-%d')  
**PROYECTO:** RAG MINEDU - Sistema Híbrido de Búsqueda Normativa