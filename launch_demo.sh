#!/bin/bash
# Launch Script para Demo de Rendimiento MINEDU Enterprise
# ========================================================

echo "🚀 MINEDU Performance Demo - Enterprise Edition"
echo "================================================"
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no encontrado. Instala Python 3.8+"
    exit 1
fi

# Verificar Streamlit
if ! command -v streamlit &> /dev/null; then
    echo "📦 Instalando Streamlit..."
    pip install streamlit
fi

# Verificar dependencias
echo "📦 Verificando dependencias..."
if [ -f "requirements_performance.txt" ]; then
    pip install -q -r requirements_performance.txt
    echo "✅ Dependencias instaladas"
else
    echo "⚠️ requirements_performance.txt no encontrado, instalando básicas..."
    pip install streamlit redis prometheus-client faiss-cpu plotly pandas
fi

# Verificar Redis (opcional)
echo "🔍 Verificando Redis..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis disponible - Cache L2 habilitado"
    else
        echo "⚠️ Redis instalado pero no ejecutándose"
        echo "💡 Ejecuta: redis-server &"
    fi
else
    echo "⚠️ Redis no instalado - Solo cache L1 disponible"
    echo "💡 Para instalar: apt-get install redis-server o brew install redis"
fi

echo ""
echo "🎯 Iniciando Demo de Rendimiento..."
echo "======================================"
echo ""
echo "📊 Acceso:"
echo "   • Demo Principal: http://localhost:8501"
echo "   • Métricas Prometheus: http://localhost:8001/metrics"
echo ""
echo "🔧 Funcionalidades:"
echo "   • Upload y procesamiento de PDFs"
echo "   • Cache multi-nivel con métricas"
echo "   • Búsqueda semántica FAISS"
echo "   • Pipeline asíncrono optimizado"
echo "   • Monitoreo Prometheus en tiempo real"
echo ""
echo "⚡ Objetivos: Latencia <0.2s, Cache >80%, Concurrencia 500+"
echo ""

# Iniciar servidor de métricas en background
echo "📈 Iniciando servidor de métricas..."
python3 metrics_server.py &
METRICS_PID=$!

# Esperar un momento para que inicie
sleep 2

# Iniciar demo Streamlit
echo "🎨 Iniciando interfaz Streamlit..."
echo ""
echo "🎉 ¡Demo listo! Abre http://localhost:8501 en tu navegador"
echo ""

# Ejecutar Streamlit
streamlit run demo_performance.py --server.port 8501 --server.headless false

# Cleanup al terminar
echo ""
echo "🛑 Deteniendo servicios..."
kill $METRICS_PID 2>/dev/null
echo "✅ Demo terminado"