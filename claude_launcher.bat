@echo off
echo 🤖 CLAUDE CODE LAUNCHER
echo ========================
echo.
echo Para usar Claude Code necesitas configurar tu API key:
echo.
echo 1. Obtén tu API key en: https://console.anthropic.com/
echo 2. Configura la variable de entorno:
echo    set ANTHROPIC_API_KEY=tu_api_key_aqui
echo.
echo 3. Ejecuta Claude Code:
echo    python claude_simple.py
echo.
echo ¿Tienes tu API key? (s/n)
set /p answer=
if "%answer%"=="s" (
    set /p apikey=Ingresa tu API key: 
    set ANTHROPIC_API_KEY=%apikey%
    echo API key configurada para esta sesión
    python claude_simple.py
) else (
    echo Configura tu API key primero en: https://console.anthropic.com/
)
pause
