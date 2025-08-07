# 🚀 CLAUDE CODE - INSTRUCCIONES PASO A PASO

## 📋 **PARA ABRIR CLAUDE CODE EN ESTE PROYECTO:**

### **MÉTODO 1: Comandos Paso a Paso (RECOMENDADO)**

**Paso 1: Abrir PowerShell**
- Presiona `Win + X` y selecciona "Windows PowerShell"
- O busca "PowerShell" en el menú inicio

**Paso 2: Activar WSL Ubuntu**
```bash
wsl -d Ubuntu
```

**Paso 3: Ir al directorio del proyecto**
```bash
cd /mnt/c/Users/hanns/Documents/proyectos/vm-expedientes-minedu
```

**Paso 4: Ejecutar Claude Code**
```bash
npx @anthropic-ai/claude-code
```

---

### **MÉTODO 2: Comando Todo en Uno (RÁPIDO)**

**Abrir PowerShell y ejecutar:**
```bash
wsl -d Ubuntu bash -c "cd /mnt/c/Users/hanns/Documents/proyectos/vm-expedientes-minedu && npx @anthropic-ai/claude-code"
```

---

### **MÉTODO 3: Usando el Script Automático**

**Ejecutar desde el directorio del proyecto:**
```bash
abrir-claude-code.bat
```

---

## 🎯 **COMANDOS ÚTILES DE CLAUDE CODE:**

### **Comando básico:**
```bash
npx @anthropic-ai/claude-code
```

### **Comando no interactivo:**
```bash
npx @anthropic-ai/claude-code --print "tu pregunta aquí"
```

### **Ver ayuda:**
```bash
npx @anthropic-ai/claude-code --help
```

### **Ver versión:**
```bash
npx @anthropic-ai/claude-code --version
```

### **Continuar conversación anterior:**
```bash
npx @anthropic-ai/claude-code --continue
```

---

## 🔧 **INFORMACIÓN TÉCNICA:**

- **Versión instalada:** 1.0.43
- **Ubicación:** @anthropic-ai/claude-code (instalado globalmente)
- **Tipo de cuenta:** Versión de pago (sin necesidad de API key)
- **WSL:** Ubuntu (no Docker Desktop)
- **Directorio proyecto:** `/mnt/c/Users/hanns/Documents/proyectos/vm-expedientes-minedu`

---

## 🚨 **SOLUCIÓN A PROBLEMAS COMUNES:**

### **Error: "bash: line 1: /home/hanns/.nvm/nvm.sh: No such file"**
- Usar directamente `npx` sin cargar nvm
- Comando: `npx @anthropic-ai/claude-code`

### **Error: "Invalid API key"**
- Ya tienes versión de pago, ignora este error
- Continúa con el comando normal

### **Error: "conda-script.py error"**
- Usar una terminal PowerShell nueva (no desde Cursor/VSCode)
- Ejecutar los comandos paso a paso

---

## 📝 **COMANDOS COMPLETOS PARA COPIAR Y PEGAR:**

### **Opción A: Paso a Paso**
```bash
# 1. Abrir WSL Ubuntu
wsl -d Ubuntu

# 2. Ir al proyecto
cd /mnt/c/Users/hanns/Documents/proyectos/vm-expedientes-minedu

# 3. Ejecutar Claude Code
npx @anthropic-ai/claude-code
```

### **Opción B: Todo en Uno**
```bash
wsl -d Ubuntu bash -c "cd /mnt/c/Users/hanns/Documents/proyectos/vm-expedientes-minedu && npx @anthropic-ai/claude-code"
```

---

## 🎯 **RECORDATORIO:**
- Siempre usar **PowerShell NUEVA** (no desde Cursor/VSCode)
- Especificar `-d Ubuntu` para usar Ubuntu WSL
- El directorio debe ser `/mnt/c/Users/hanns/Documents/proyectos/vm-expedientes-minedu`

---

**¡Guarda este archivo para futuras referencias!** 📌 