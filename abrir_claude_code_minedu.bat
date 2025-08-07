@echo off
title Claude Code - VM Expedientes MINEDU
echo 🚀 Iniciando Claude Code...
echo 📁 Proyecto: VM-EXPEDIENTES-MINEDU
echo.

:: Cambiar al directorio del proyecto
cd /d "C:\Users\hanns\Documents\proyectos\vm-expedientes-minedu"

:: Abrir Claude Code en el directorio actual
code .

:: Si code no funciona, intentar con cursor
if %errorlevel% neq 0 (
    echo ⚠️  Intentando con cursor...
    cursor .
)

:: Si ninguno funciona, mostrar mensaje
if %errorlevel% neq 0 (
    echo ❌ Error: No se pudo abrir Claude Code
    echo 💡 Asegúrate de que esté instalado correctamente
    pause
) 