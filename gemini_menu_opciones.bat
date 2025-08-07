@echo off
title Gemini CLI - Menu de Opciones
color 0B
:menu
cls
echo.
echo 🤖 ========================================
echo     GEMINI CLI - MENU DE OPCIONES
echo ========================================
echo.
echo    1. 🚀 Ejecutar Gemini CLI (Auto)
echo    2. 🔧 Instalar Gemini CLI globalmente
echo    3. 📦 Usar versión temporal (npx)
echo    4. 🔑 Configurar API Key
echo    5. 📚 Ver información de uso
echo    6. ❌ Salir
echo.
set /p opcion="Selecciona una opción (1-6): "

if "%opcion%"=="1" goto ejecutar_auto
if "%opcion%"=="2" goto instalar_global
if "%opcion%"=="3" goto usar_npx
if "%opcion%"=="4" goto configurar_api
if "%opcion%"=="5" goto mostrar_info
if "%opcion%"=="6" goto salir
goto menu

:ejecutar_auto
cls
echo 🚀 Ejecutando Gemini CLI automáticamente...
cd /d "C:\Users\hanns\Documents\proyectos\vm-expedientes-minedu"
where gemini >nul 2>&1
if %errorlevel% equ 0 (
    gemini
) else (
    npx https://github.com/google-gemini/gemini-cli
)
goto fin

:instalar_global
cls
echo 🔧 Instalando Gemini CLI globalmente...
npm install -g @google/gemini-cli
echo.
echo ✅ Instalación completada
pause
goto menu

:usar_npx
cls
echo 📦 Usando versión temporal con npx...
cd /d "C:\Users\hanns\Documents\proyectos\vm-expedientes-minedu"
npx https://github.com/google-gemini/gemini-cli
goto fin

:configurar_api
cls
echo 🔑 Configuración de API Key
echo.
echo Para usar tu propia API key de Google AI Studio:
echo 1. Ve a https://aistudio.google.com/
echo 2. Crea una API key
echo 3. Ejecuta: set GEMINI_API_KEY=TU_API_KEY
echo.
set /p api_key="Ingresa tu API key (o presiona Enter para omitir): "
if not "%api_key%"=="" (
    set GEMINI_API_KEY=%api_key%
    echo ✅ API Key configurada para esta sesión
)
pause
goto menu

:mostrar_info
cls
echo 📚 INFORMACIÓN DE USO - GEMINI CLI
echo.
echo 🔗 Autenticación:
echo    - Se abre navegador para login con Google
echo    - O configura GEMINI_API_KEY
echo.
echo ⚡ Límites gratuitos:
echo    - 60 solicitudes por minuto
echo    - 1000 solicitudes diarias
echo    - Gemini 2.5 Pro incluido
echo.
echo 💡 Comandos útiles en Gemini:
echo    - "Describe la arquitectura de este proyecto"
echo    - "Corrige este bug en el archivo X"
echo    - "Genera pruebas unitarias"
echo    - Usa @ para subir archivos
echo.
echo 📚 Documentación: https://github.com/google-gemini/gemini-cli
echo.
pause
goto menu

:salir
echo 👋 ¡Hasta luego!
exit

:fin
echo.
echo ✅ Sesión terminada
pause 