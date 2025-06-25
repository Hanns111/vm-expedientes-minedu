#!/bin/bash

# Script de prueba para el endpoint /search del API MINEDU
# Servidor: http://127.0.0.1:8001
# Autor: Claude Code
# Fecha: 2025-06-24

echo "=================================================="
echo "🔍 PRUEBAS DEL ENDPOINT /search - API MINEDU"
echo "=================================================="
echo "Servidor: http://127.0.0.1:8001"
echo "Endpoint: /search"
echo "Método: POST"
echo ""

# Configuración
API_URL="http://127.0.0.1:8001/search"
HEADERS="Content-Type: application/json"

# Función para hacer la solicitud y mostrar resultado
test_search() {
    local test_number=$1
    local question=$2
    
    echo "=================================================="
    echo "🧪 PRUEBA $test_number"
    echo "=================================================="
    echo "Pregunta: $question"
    echo ""
    echo "📤 Enviando solicitud..."
    
    # Crear el JSON payload con clave "query"
    local json_payload="{\"query\": \"$question\"}"
    
    echo "JSON enviado: $json_payload"
    echo "---------------------------------------------"
    
    # Realizar la solicitud con curl y capturar código HTTP
    local response=$(curl -s -X POST "$API_URL" \
        -H "$HEADERS" \
        -d "$json_payload" \
        --max-time 30 \
        --connect-timeout 10 \
        -w "HTTPSTATUS:%{http_code}")
    
    # Verificar si curl fue exitoso
    local curl_exit_code=$?
    
    if [ $curl_exit_code -ne 0 ]; then
        echo "❌ ERROR: No se pudo conectar al servidor"
        echo "Código de salida de curl: $curl_exit_code"
        echo "Verifica que el servidor esté ejecutándose en http://127.0.0.1:8001"
    else
        # Extraer código HTTP y respuesta
        local http_code=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
        local response_body=$(echo "$response" | sed 's/HTTPSTATUS:[0-9]*$//')
        
        echo "📥 Código HTTP: $http_code"
        echo "📥 Respuesta del servidor:"
        echo "---------------------------------------------"
        
        if [ "$http_code" = "422" ]; then
            echo "🚨 VALIDATION ERROR (422):"
            echo "$response_body" | python3 -m json.tool 2>/dev/null || echo "$response_body"
        elif [ "$http_code" = "200" ]; then
            # Verificar si contiene campo "results"
            if [[ "$response_body" == *"\"results\""* ]]; then
                echo "✅ PASS #$test_number: HTTP 200 OK + campo results encontrado"
                echo ""
                echo "$response_body" | python3 -m json.tool 2>/dev/null || echo "$response_body"
            else
                echo "❌ FAIL #$test_number: falta campo \"results\""
                echo ""
                echo "$response_body" | python3 -m json.tool 2>/dev/null || echo "$response_body"
            fi
        else
            echo "📄 HTTP $http_code - Respuesta:"
            echo "$response_body" | python3 -m json.tool 2>/dev/null || echo "$response_body"
        fi
    fi
    
    echo ""
    echo "---------------------------------------------"
    echo "✅ Prueba $test_number completada"
    echo ""
}

# Ejecutar las tres pruebas
echo "🚀 Iniciando pruebas..."
echo ""

# Prueba 1
test_search "1" "¿Cuál es el objetivo de la directiva de viáticos?"

# Prueba 2  
test_search "2" "¿Qué entidad aprueba esta directiva?"

# Prueba 3
test_search "3" "¿Cuánto es el monto máximo permitido por día en Lima?"

echo "=================================================="
echo "🎯 RESUMEN DE PRUEBAS COMPLETADAS"
echo "=================================================="
echo "✅ Se ejecutaron 3 pruebas al endpoint /search"
echo "📊 Endpoint probado: $API_URL"
echo "🕒 Tiempo de espera máximo: 30 segundos por solicitud"
echo ""
echo "💡 Para validar automáticamente las respuestas,"
echo "   ejecuta: ./test_search_with_validation.sh"
echo ""
echo "=================================================="
echo "🏁 PRUEBAS FINALIZADAS"
echo "=================================================="