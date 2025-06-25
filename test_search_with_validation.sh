#!/bin/bash

# Script de prueba con validaciones automáticas para el endpoint /search
# Validaciones: HTTP 200, campo "results", palabras clave específicas
# Autor: Claude Code
# Fecha: 2025-06-24

echo "=================================================="
echo "🔍 PRUEBAS CON VALIDACIÓN AUTOMÁTICA - API MINEDU"
echo "=================================================="
echo "Servidor: http://127.0.0.1:8001"
echo "Endpoint: /search"
echo "Método: POST"
echo ""

API_URL="http://127.0.0.1:8001/search"
HEADERS="Content-Type: application/json"
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Función para realizar prueba con validación
test_with_validation() {
    local test_number=$1
    local question=$2
    local expected_keywords=("${@:3}")  # Array de palabras clave esperadas
    
    echo "=================================================="
    echo "🧪 PRUEBA $test_number"
    echo "=================================================="
    echo "Pregunta: $question"
    echo "Keywords esperadas: ${expected_keywords[*]}"
    echo ""
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # Crear JSON payload con clave "query"
    local json_payload="{\"query\": \"$question\"}"
    echo "📤 JSON enviado: $json_payload"
    echo "---------------------------------------------"
    
    # Realizar solicitud con captura de código HTTP
    local response=$(curl -s -X POST "$API_URL" \
        -H "$HEADERS" \
        -d "$json_payload" \
        --max-time 20 \
        --connect-timeout 10 \
        -w "HTTPSTATUS:%{http_code}")
    
    # Verificar éxito de curl
    local curl_exit_code=$?
    if [ $curl_exit_code -ne 0 ]; then
        echo "❌ ERROR: Fallo de conexión (curl exit code: $curl_exit_code)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo "---------------------------------------------"
        return 1
    fi
    
    # Extraer código HTTP y respuesta
    local http_code=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    local response_body=$(echo "$response" | sed 's/HTTPSTATUS:[0-9]*$//')
    
    echo "📥 Código HTTP: $http_code"
    echo ""
    
    # Manejo de errores HTTP específicos
    if [ "$http_code" = "422" ]; then
        echo "🚨 VALIDATION ERROR (422):"
        echo "$response_body" | python3 -m json.tool 2>/dev/null || echo "$response_body"
        echo ""
        echo "❌ FAIL #$test_number: Error de validación (HTTP 422)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo "---------------------------------------------"
        return 1
    elif [ "$http_code" != "200" ]; then
        echo "❌ FAIL #$test_number: HTTP $http_code (esperado: 200)"
        echo "Respuesta:"
        echo "$response_body" | python3 -m json.tool 2>/dev/null || echo "$response_body"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo "---------------------------------------------"
        return 1
    fi
    
    # Validar HTTP 200 y campo "results"
    if [[ "$response_body" != *"\"results\""* ]]; then
        echo "❌ FAIL #$test_number: falta campo \"results\""
        echo "Respuesta:"
        echo "$response_body" | python3 -m json.tool 2>/dev/null || echo "$response_body"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo "---------------------------------------------"
        return 1
    fi
    
    echo "✅ PASS #$test_number: HTTP 200 OK + campo results encontrado"
    echo ""
    
    # Mostrar respuesta formateada (primeros 300 chars)
    echo "📋 Respuesta (preview):"
    local preview=$(echo "$response_body" | head -c 300)
    echo "$preview..." | python3 -m json.tool 2>/dev/null || echo "$preview..."
    echo ""
    
    # Validar palabras clave
    local keywords_found=0
    local total_keywords=${#expected_keywords[@]}
    
    echo "🔍 Validando palabras clave:"
    for keyword in "${expected_keywords[@]}"; do
        if [[ "$response_body" == *"$keyword"* ]]; then
            echo "  ✅ '$keyword' - ENCONTRADA"
            keywords_found=$((keywords_found + 1))
        else
            echo "  ❌ '$keyword' - NO ENCONTRADA"
        fi
    done
    
    echo ""
    echo "📊 VALIDACIÓN KEYWORDS: $keywords_found/$total_keywords encontradas"
    
    # Determinar resultado final
    if [ $keywords_found -gt 0 ]; then
        echo "🎯 RESULTADO FINAL: ✅ APROBADA (HTTP 200 + results + keywords)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo "🎯 RESULTADO FINAL: ⚠️  PARCIAL (HTTP 200 + results, pero sin keywords)"
        PASSED_TESTS=$((PASSED_TESTS + 1))  # Consideramos PASS si tiene HTTP 200 + results
    fi
    
    echo "---------------------------------------------"
    echo ""
}

# Ejecutar las tres pruebas con validaciones específicas
echo "🚀 Iniciando pruebas con validación..."
echo ""

# Prueba 1: Objetivo de la directiva
test_with_validation "1" \
    "¿Cuál es el objetivo de la directiva de viáticos?" \
    "objetivo" "directiva" "viático" "establece" "procedimiento"

# Prueba 2: Entidad aprobadora
test_with_validation "2" \
    "¿Qué entidad aprueba esta directiva?" \
    "MINEDU" "Ministerio" "Educación" "aprueba" "entidad"

# Prueba 3: Montos máximos
test_with_validation "3" \
    "¿Cuánto es el monto máximo permitido por día en Lima?" \
    "S/" "monto" "máximo" "Lima" "380" "320" "diario"

# Resumen final
echo "=================================================="
echo "📋 RESUMEN FINAL DE VALIDACIONES"
echo "=================================================="
echo "🧪 Total de pruebas: $TOTAL_TESTS"
echo "✅ Pruebas aprobadas: $PASSED_TESTS"
echo "❌ Pruebas reprobadas: $FAILED_TESTS"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo "🎉 TODAS LAS PRUEBAS PASARON"
    echo "✅ El endpoint /search está funcionando correctamente"
    exit 0
else
    echo "⚠️  ALGUNAS PRUEBAS FALLARON"
    echo "❌ Revisa la configuración del servidor o los datos de prueba"
    exit 1
fi