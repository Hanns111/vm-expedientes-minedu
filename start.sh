#!/bin/bash
# start.sh - Script de inicio unificado para el sistema MINEDU RAG

echo "🚀 Iniciando Sistema MINEDU RAG Híbrido..."
echo "================================================"

# Función para manejar la limpieza al salir
cleanup() {
    echo ""
    echo "🛑 Deteniendo servicios..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "  ✅ Backend detenido"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "  ✅ Frontend detenido"
    fi
    echo "👋 ¡Hasta luego!"
    exit 0
}

# Configurar trap para cleanup
trap cleanup SIGINT SIGTERM

# Verificar que estamos en la raíz del proyecto
if [ ! -f "demo_secure.py" ]; then
    echo "❌ Error: Este script debe ejecutarse desde la raíz del proyecto"
    echo "   Asegúrate de estar en el directorio vm-expedientes-minedu/"
    exit 1
fi

# Verificar que existen los vectorstores
if [ ! -f "data/vectorstores/bm25.pkl" ]; then
    echo "⚠️  Advertencia: No se encuentran vectorstores en data/vectorstores/"
    echo "   El sistema funcionará en modo fallback"
    echo "   Para generar vectorstores, ejecuta: python src/ai/generate_vectorstore_full_v2.py"
fi

# Backend
echo "📦 Iniciando Backend en puerto 8001..."
cd backend
python src/main.py &
BACKEND_PID=$!
cd ..

# Esperar a que el backend esté listo
echo "⏳ Esperando que el backend esté listo..."
sleep 3

# Verificar que el backend responde
if curl -s http://localhost:8001/health > /dev/null; then
    echo "  ✅ Backend activo en http://localhost:8001"
else
    echo "  ❌ Backend no responde - verificando logs..."
    sleep 2
fi

# Frontend
echo "🎨 Iniciando Frontend en puerto 3000..."
cd frontend-new
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Sistema iniciado correctamente!"
echo "================================================"
echo "   🔧 Backend API: http://localhost:8001"
echo "   🖥️  Frontend:   http://localhost:3000"
echo "   📚 Docs API:    http://localhost:8001/docs"
echo ""
echo "💡 Consultas de prueba sugeridas:"
echo "   - ¿Cuál es el monto máximo para viáticos de ministros?"
echo "   - ¿Qué límites tiene la declaración jurada?"
echo "   - ¿Cuánto es el viático para servidores civiles?"
echo ""
echo "⚡ El sistema está listo para usar!"
echo "   Presiona Ctrl+C para detener ambos servicios"

# Esperar indefinidamente hasta que el usuario presione Ctrl+C
wait