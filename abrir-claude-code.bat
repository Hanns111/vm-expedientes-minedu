@echo off
echo 🚀 ABRIENDO CLAUDE CODE
echo ========================
echo.
echo Ejecutando WSL Ubuntu...
wsl -d Ubuntu bash -c "cd /mnt/c/Users/hanns/Documents/proyectos/vm-expedientes-minedu && npx @anthropic-ai/claude-code"
pause
