@echo off
title Gemini CLI - VM Expedientes MINEDU
color 0A
echo.
echo 🤖 ================================
echo    GEMINI CLI - MINEDU PROJECT
echo ================================
echo.
echo 📁 Proyecto: VM-EXPEDIENTES-MINEDU
echo 🔗 Conexión: Google Gemini 2.5 Pro
echo ⚡ Límites: 60 req/min - 1000 diarias
echo.

:: Cambiar al directorio del proyecto
cd /d "C:\Users\hanns\Documents\proyectos\vm-expedientes-minedu"
echo 📂 Directorio: %cd%
echo.

:: Verificar si Gemini CLI está instalado globalmente
where gemini >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Gemini CLI instalado globalmente
    echo 🚀 Ejecutando: gemini
    echo.
    gemini
) else (
    echo ⚠️  Gemini CLI no instalado globalmente
    echo 🔄 Usando instalación temporal con npx...
    echo.
    echo 💡 Para instalación permanente ejecuta:
    echo    npm install -g @google/gemini-cli
    echo.
    echo 🚀 Ejecutando: npx https://github.com/google-gemini/gemini-cli
    echo.
    npx https://github.com/google-gemini/gemini-cli
)

:: Si hay error, mostrar ayuda
if %errorlevel% neq 0 (
    echo.
    echo ❌ Error al ejecutar Gemini CLI
    echo.
    echo 🔧 SOLUCIONES POSIBLES:
    echo    1. Verificar conexión a internet
    echo    2. Instalar Node.js si no está instalado
    echo    3. Ejecutar: npm install -g @google/gemini-cli
    echo    4. Configurar API key si es necesario:
    echo       set GEMINI_API_KEY=TU_API_KEY
    echo.
    echo 📚 Documentación: https://github.com/google-gemini/gemini-cli
    echo.
)

echo.
echo 🔄 Presiona cualquier tecla para salir...
pause >nul 