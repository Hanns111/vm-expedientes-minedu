#!/bin/bash
# ==============================================
# 🔍 SCRIPT DE VERIFICACIÓN V2.0 - VM-EXPEDIENTES-MINEDU
# Protocolo obligatorio antes de cualquier implementación
# ==============================================
set -euo pipefail

# Timeout global de 60 segundos
TIMEOUT=60

echo "=== VERIFICACIÓN V2.0 INICIADA ==="
echo "timestamp:$(date -u +"%Y-%m-%dT%H:%MZ")"

# ==============================================
# 1. CONTEO DE ARCHIVOS PYTHON
# ==============================================
echo "=== CONTEO ARCHIVOS PYTHON ==="
PYTHON_TOTAL=$(find . -name "*.py" -type f | wc -l)
PYTHON_SIN_VENV=$(find . -name "*.py" -not -path "./venv*" -not -path "./.next/*" -type f | wc -l)
echo "python_total:$PYTHON_TOTAL"
echo "python_sin_venv:$PYTHON_SIN_VENV"

# ==============================================
# 2. VERIFICACIÓN LEGALREASONER
# ==============================================
echo "=== MOTOR LEGAL ==="
LEGAL_FILE="backend/src/domain/legal_reasoning.py"
if [[ -f "$LEGAL_FILE" ]]; then
    LEGAL_LINES=$(wc -l < "$LEGAL_FILE")
    LEGAL_CLASS=$(grep -c "class LegalReasoner" "$LEGAL_FILE" || echo "0")
    echo "legal_file_exists:true"
    echo "legal_lines:$LEGAL_LINES"
    echo "legal_class_found:$LEGAL_CLASS"
else
    echo "legal_file_exists:false"
    echo "legal_lines:0"
    echo "legal_class_found:0"
fi

# ==============================================
# 3. ESTADO DE PUERTOS
# ==============================================
echo "=== ESTADO PUERTOS ==="

# Puerto 8001 (Backend)
if timeout 5 curl -s --fail http://localhost:8001/health >/dev/null 2>&1; then
    echo "port_8001:active"
    BACKEND_RESPONSE=$(timeout 5 curl -s http://localhost:8001/health 2>/dev/null || echo "error")
    echo "backend_response:$BACKEND_RESPONSE"
else
    echo "port_8001:inactive"
    echo "backend_response:error"
fi

# Puerto 3000 (Frontend)
if timeout 5 curl -s --fail http://localhost:3000 >/dev/null 2>&1; then
    echo "port_3000:active"
else
    echo "port_3000:inactive"
fi

# ==============================================
# 4. VECTORSTORES SHA-256
# ==============================================
echo "=== VECTORSTORES SHA-256 ==="
VECTORSTORE_DIR="data/vectorstores"
if [[ -d "$VECTORSTORE_DIR" ]]; then
    echo "vectorstore_dir_exists:true"
    
    # Contar archivos .pkl
    PKL_COUNT=$(find "$VECTORSTORE_DIR" -name "*.pkl" -type f | wc -l)
    echo "pkl_files_count:$PKL_COUNT"
    
    # SHA-256 de cada archivo .pkl
    if [[ $PKL_COUNT -gt 0 ]]; then
        for pkl_file in "$VECTORSTORE_DIR"/*.pkl; do
            if [[ -f "$pkl_file" ]]; then
                filename=$(basename "$pkl_file" .pkl)
                sha256_hash=$(sha256sum "$pkl_file" | cut -d' ' -f1)
                file_size=$(stat -c%s "$pkl_file")
                echo "${filename}_sha256:$sha256_hash"
                echo "${filename}_size:$file_size"
            fi
        done
    else
        echo "vectorstore_sha256:no_files"
    fi
else
    echo "vectorstore_dir_exists:false"
    echo "pkl_files_count:0"
fi

# ==============================================
# 5. CHUNKS VERIFICACIÓN
# ==============================================
echo "=== CHUNKS VERIFICACIÓN ==="
CHUNKS_FILE="data/processed/chunks.json"
if [[ -f "$CHUNKS_FILE" ]]; then
    echo "chunks_file_exists:true"
    CHUNKS_SIZE=$(stat -c%s "$CHUNKS_FILE")
    CHUNKS_LINES=$(wc -l < "$CHUNKS_FILE")
    echo "chunks_size:$CHUNKS_SIZE"
    echo "chunks_lines:$CHUNKS_LINES"
    
    # Intentar contar objetos JSON (aproximado)
    CHUNKS_COUNT=$(grep -c '"id"' "$CHUNKS_FILE" 2>/dev/null || echo "error")
    echo "chunks_count:$CHUNKS_COUNT"
else
    echo "chunks_file_exists:false"
    echo "chunks_size:0"
    echo "chunks_count:0"
fi

# ==============================================
# 6. PROCESOS ACTIVOS
# ==============================================
echo "=== PROCESOS ACTIVOS ==="
PYTHON_PROCESSES=$(ps aux | grep -E 'python.*main.py|uvicorn|serve_frontend' | grep -v grep | wc -l)
echo "python_processes_count:$PYTHON_PROCESSES"

# ==============================================
# 7. TIMESTAMP FINAL
# ==============================================
echo "=== VERIFICACIÓN COMPLETADA ==="
echo "verification_completed:true"
echo "verification_duration:$SECONDS"
echo "end_timestamp:$(date -u +"%Y-%m-%dT%H:%MZ")"

# ==============================================
# 8. SALIDA ESTRUCTURADA FINAL
# ==============================================
echo ""
echo "===RESULT==="
echo "python_files_total=$PYTHON_TOTAL"
echo "python_files_clean=$PYTHON_SIN_VENV"
echo "legal_reasoner_lines=${LEGAL_LINES:-0}"
echo "legal_class_found=${LEGAL_CLASS:-0}"
if timeout 5 curl -s --fail http://localhost:8001/health >/dev/null 2>&1; then
    echo "backend_basic=healthy"
else
    echo "backend_basic=inactive"
fi
if timeout 5 curl -s --fail http://localhost:8001/api/chat/professional >/dev/null 2>&1; then
    echo "backend_professional=healthy"
else
    echo "backend_professional=503"
fi
echo "vectorstore_files=${PKL_COUNT:-0}"
echo "chunks_objects=${CHUNKS_COUNT:-0}"
echo "python_processes=${PYTHON_PROCESSES:-0}"
if [[ -d "$VECTORSTORE_DIR" && $PKL_COUNT -gt 0 ]]; then
    for pkl_file in "$VECTORSTORE_DIR"/*.pkl; do
        if [[ -f "$pkl_file" ]]; then
            filename=$(basename "$pkl_file" .pkl)
            sha256_hash=$(sha256sum "$pkl_file" | cut -d' ' -f1)
            echo "vector_${filename}_sha=${sha256_hash}"
        fi
    done
fi
echo "===END==="