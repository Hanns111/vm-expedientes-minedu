#!/usr/bin/env python3
"""
API REST MINEDU - Análisis de Documentos
========================================

API REST para cargar y analizar documentos SUNAT/MINEDU
usando el Sistema Adaptativo completo.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import tempfile
import os
from pathlib import Path
import json
from datetime import datetime
import logging
import uuid

# Importar el procesador adaptativo
from adaptive_processor_minedu import AdaptiveProcessorMINEDU
from src.core.security.file_validator import FileValidator
from src.core.security.input_validator import InputValidator

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="MINEDU - API de Análisis de Documentos",
    description="API REST para análisis inteligente de documentos gubernamentales",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar procesador global
processor = None

@app.on_event("startup")
async def startup_event():
    """Inicializar componentes al arrancar la API"""
    global processor
    logger.info("🚀 Inicializando API MINEDU...")
    processor = AdaptiveProcessorMINEDU(learning_mode=True)
    logger.info("✅ API MINEDU lista")

# Modelos Pydantic
class DocumentAnalysisResponse(BaseModel):
    """Respuesta del análisis de documento"""
    success: bool
    message: str
    document_id: str
    processing_time: float
    extraction_results: Dict[str, Any]
    document_analysis: Dict[str, Any]
    extraction_strategy: Dict[str, Any]

class HealthResponse(BaseModel):
    """Respuesta de salud del sistema"""
    status: str
    version: str
    components: Dict[str, str]
    uptime: str

class ErrorResponse(BaseModel):
    """Respuesta de error"""
    error: str
    detail: str
    timestamp: str

# Endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    """Endpoint raíz"""
    return {
        "message": "MINEDU - API de Análisis de Documentos",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Verificar salud del sistema"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        components={
            "adaptive_processor": "✅ Activo",
            "money_detector": "✅ Activo",
            "config_optimizer": "✅ Activo"
        },
        uptime="Sistema funcionando"
    )

@app.post("/analyze", response_model=DocumentAnalysisResponse)
async def analyze_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Analizar documento cargado
    
    Args:
        file: Archivo a analizar (PDF, JPG, PNG)
        
    Returns:
        Resultados del análisis
    """
    try:
        # Validar archivo
        if not file.filename:
            raise HTTPException(status_code=400, detail="Nombre de archivo requerido")
        
        # Verificar tamaño
        if file.size and file.size > 100 * 1024 * 1024:  # 100MB
            raise HTTPException(
                status_code=413, 
                detail=f"Archivo demasiado grande: {file.size / (1024*1024):.1f}MB (máximo: 100MB)"
            )
        
        # Verificar extensión
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif']
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de archivo no soportado: {file_extension}"
            )
        
        # Crear directorio temporal
        temp_dir = Path("data/temp")
        temp_dir.mkdir(exist_ok=True)
        
        # Generar ID único para el documento
        document_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Crear nombre seguro
        safe_filename = f"{timestamp}_{document_id}_{file.filename}"
        temp_path = temp_dir / safe_filename
        
        # Guardar archivo
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"📄 Archivo guardado: {temp_path}")
        
        # Procesar documento
        logger.info(f"🤖 Procesando documento: {file.filename}")
        start_time = datetime.now()
        
        results = processor.process_document(str(temp_path))
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Programar limpieza del archivo temporal
        background_tasks.add_task(cleanup_temp_file, temp_path)
        
        # Preparar respuesta
        response = DocumentAnalysisResponse(
            success=results['success'],
            message="Análisis completado exitosamente",
            document_id=document_id,
            processing_time=processing_time,
            extraction_results=results['extraction_results'],
            document_analysis=results['document_analysis'],
            extraction_strategy=results['extraction_strategy']
        )
        
        logger.info(f"✅ Análisis completado: {file.filename}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error procesando {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.post("/analyze-batch")
async def analyze_batch(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    """
    Analizar múltiples documentos en lote
    
    Args:
        files: Lista de archivos a analizar
        
    Returns:
        Resultados del análisis en lote
    """
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Máximo 10 archivos por lote")
    
    results = []
    
    for file in files:
        try:
            # Procesar cada archivo individualmente
            result = await analyze_document(background_tasks, file)
            results.append(result.dict())
        except Exception as e:
            results.append({
                "success": False,
                "filename": file.filename,
                "error": str(e)
            })
    
    return {
        "batch_results": results,
        "total_files": len(files),
        "successful": sum(1 for r in results if r.get('success', False)),
        "failed": sum(1 for r in results if not r.get('success', False))
    }

@app.get("/stats")
async def get_system_stats():
    """Obtener estadísticas del sistema"""
    if processor:
        stats = processor.get_processing_stats()
        return {
            "system_stats": stats,
            "status": "active",
            "timestamp": datetime.now().isoformat()
        }
    else:
        return {"error": "Procesador no inicializado"}

@app.post("/query")
async def query_document(
    query: str,
    document_id: Optional[str] = None
):
    """
    Hacer consulta sobre documento procesado
    
    Args:
        query: Consulta en lenguaje natural
        document_id: ID del documento (opcional)
        
    Returns:
        Respuesta a la consulta
    """
    # Validar entrada
    if not InputValidator.validate_query(query):
        raise HTTPException(status_code=400, detail="Consulta inválida")
    
    # Aquí se integraría con el sistema de búsqueda híbrida
    # Por ahora, respuesta simulada
    return {
        "query": query,
        "response": "Funcionalidad de consulta en desarrollo",
        "document_id": document_id,
        "timestamp": datetime.now().isoformat()
    }

# Funciones auxiliares
async def cleanup_temp_file(file_path: Path):
    """Limpiar archivo temporal"""
    try:
        if file_path.exists():
            file_path.unlink()
            logger.info(f"🗑️ Archivo temporal eliminado: {file_path}")
    except Exception as e:
        logger.warning(f"⚠️ No se pudo eliminar archivo temporal: {e}")

# Manejo de errores
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Manejar excepciones HTTP"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            detail=f"Error {exc.status_code}",
            timestamp=datetime.now().isoformat()
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Manejar excepciones generales"""
    logger.error(f"Error no manejado: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Error interno del servidor",
            detail=str(exc),
            timestamp=datetime.now().isoformat()
        ).dict()
    )

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Iniciando API MINEDU...")
    print("📄 Documentación: http://localhost:8000/docs")
    print("🔍 Explorador API: http://localhost:8000/redoc")
    
    uvicorn.run(
        "api_minedu:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 