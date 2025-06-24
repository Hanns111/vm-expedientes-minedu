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
import time

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
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "https://ai.minedu.gob.pe",
        "*"  # Permitir todos durante desarrollo
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Inicializar procesador global y sistema de búsqueda
processor = None
hybrid_search = None

@app.on_event("startup")
async def startup_event():
    """Inicializar componentes al arrancar la API"""
    global processor, hybrid_search
    logger.info("🚀 Inicializando API MINEDU...")
    processor = AdaptiveProcessorMINEDU(learning_mode=True)
    
    # Inicializar sistema de búsqueda híbrida
    try:
        from src.core.hybrid.hybrid_search import HybridSearch
        vectorstore_path = Path("data/vectorstores")
        
        if all([
            (vectorstore_path / "bm25.pkl").exists(),
            (vectorstore_path / "tfidf.pkl").exists(),
            (vectorstore_path / "transformers.pkl").exists()
        ]):
            hybrid_search = HybridSearch(
                bm25_vectorstore_path=str(vectorstore_path / "bm25.pkl"),
                tfidf_vectorstore_path=str(vectorstore_path / "tfidf.pkl"),
                transformer_vectorstore_path=str(vectorstore_path / "transformers.pkl"),
                fusion_strategy='weighted'
            )
            logger.info("✅ Sistema de búsqueda híbrida inicializado")
        else:
            logger.warning("⚠️ Vectorstores no encontrados, solo funciones de análisis disponibles")
            
    except Exception as e:
        logger.warning(f"⚠️ No se pudo inicializar búsqueda híbrida: {e}")
    
    logger.info("✅ API MINEDU lista")

# Modelos Pydantic para el frontend
class SearchRequest(BaseModel):
    """Solicitud de búsqueda"""
    query: str
    method: Optional[str] = 'hybrid'
    top_k: Optional[int] = 10
    fusion_method: Optional[str] = 'weighted'

class SearchResult(BaseModel):
    """Resultado individual de búsqueda"""
    content: str
    score: float
    metadata: Dict[str, Any]

class SearchResponse(BaseModel):
    """Respuesta de búsqueda"""
    results: List[SearchResult]
    query: str
    method: str
    processing_time: float
    total_results: int
    metrics: Optional[Dict[str, float]] = None

class DocumentUploadResponse(BaseModel):
    """Respuesta de subida de documento"""
    document_id: str
    filename: str
    status: str
    message: str

class SystemStatus(BaseModel):
    """Estado del sistema"""
    status: str
    version: str
    uptime: float
    active_searches: int
    vectorstores: Dict[str, bool]

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

@app.get("/health", response_model=SystemStatus)
async def health_check():
    """Verificar salud del sistema compatible con frontend"""
    global hybrid_search
    
    # Verificar estado de vectorstores
    vectorstore_path = Path("data/vectorstores")
    vectorstores_status = {
        "bm25": (vectorstore_path / "bm25.pkl").exists(),
        "tfidf": (vectorstore_path / "tfidf.pkl").exists(),
        "transformers": (vectorstore_path / "transformers.pkl").exists()
    }
    
    # Determinar estado general
    system_status = "healthy" if any(vectorstores_status.values()) else "degraded"
    
    return SystemStatus(
        status=system_status,
        version="2.0.0",
        uptime=time.time(),  # Simplicado para demo
        active_searches=0,  # En producción sería un contador real
        vectorstores=vectorstores_status
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

@app.post("/search", response_model=SearchResponse)
async def search_documents(search_request: SearchRequest):
    """
    Realizar búsqueda híbrida en documentos MINEDU
    
    Args:
        search_request: Solicitud de búsqueda con parámetros
        
    Returns:
        Resultados de búsqueda formateados para frontend
    """
    global hybrid_search
    
    if not hybrid_search:
        raise HTTPException(
            status_code=503,
            detail="Sistema de búsqueda no disponible. Verifica que los vectorstores existan."
        )
    
    # Validar entrada
    if not InputValidator.validate_query(search_request.query):
        raise HTTPException(status_code=400, detail="Consulta contiene caracteres no válidos")
    
    try:
        start_time = time.time()
        logger.info(f"🔍 Búsqueda: '{search_request.query}' con método {search_request.method}")
        
        # Realizar búsqueda según el método especificado
        if search_request.method == 'hybrid':
            results = hybrid_search.search(
                query=search_request.query,
                top_k=search_request.top_k,
                use_methods=['bm25', 'tfidf', 'transformer']
            )
        elif search_request.method == 'bm25' and hybrid_search.bm25_retriever:
            results = hybrid_search.bm25_retriever.search(search_request.query, search_request.top_k)
        elif search_request.method == 'tfidf' and hybrid_search.tfidf_retriever:
            results = hybrid_search.tfidf_retriever.search(search_request.query, search_request.top_k)
        elif search_request.method == 'transformers' and hybrid_search.transformer_retriever:
            results = hybrid_search.transformer_retriever.search(search_request.query, search_request.top_k)
        else:
            # Fallback a híbrido
            results = hybrid_search.search(search_request.query, search_request.top_k)
        
        processing_time = time.time() - start_time
        
        # Formatear resultados para el frontend
        formatted_results = []
        for result in results:
            formatted_results.append(SearchResult(
                content=result.get('texto', result.get('text', str(result))),
                score=float(result.get('score', 0.0)),
                metadata={
                    'chunk_id': result.get('index', ''),
                    'source_document': result.get('metadatos', {}).get('source', 'documento_minedu'),
                    'page_number': result.get('metadatos', {}).get('page', None),
                    'section': result.get('metadatos', {}).get('section', None),
                    'method': result.get('method', search_request.method)
                }
            ))
        
        return SearchResponse(
            results=formatted_results,
            query=search_request.query,
            method=search_request.method,
            processing_time=processing_time,
            total_results=len(formatted_results),
            metrics={
                'processing_time_ms': processing_time * 1000,
                'avg_score': sum(r.score for r in formatted_results) / len(formatted_results) if formatted_results else 0.0
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error en búsqueda: {e}")
        raise HTTPException(status_code=500, detail=f"Error en búsqueda: {str(e)}")

@app.post("/query")
async def query_document(
    query: str,
    document_id: Optional[str] = None
):
    """
    Hacer consulta sobre documento procesado (endpoint legacy)
    
    Args:
        query: Consulta en lenguaje natural
        document_id: ID del documento (opcional)
        
    Returns:
        Respuesta a la consulta
    """
    # Redirigir al nuevo endpoint de búsqueda
    search_request = SearchRequest(query=query, method='hybrid', top_k=5)
    return await search_documents(search_request)

@app.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document_frontend(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = None,
    description: Optional[str] = None
):
    """
    Subir documento para procesamiento (endpoint para frontend)
    
    Args:
        file: Archivo a subir
        title: Título opcional del documento
        description: Descripción opcional
        
    Returns:
        Respuesta de subida formateada para frontend
    """
    try:
        # Procesar documento usando el endpoint existente
        analysis_result = await analyze_document(background_tasks, file)
        
        # Formatear respuesta para frontend
        if analysis_result.success:
            status = "completed"
            message = f"Documento '{file.filename}' procesado exitosamente"
        else:
            status = "error"
            message = f"Error procesando '{file.filename}'"
        
        return DocumentUploadResponse(
            document_id=analysis_result.document_id,
            filename=file.filename,
            status=status,
            message=message
        )
        
    except HTTPException as e:
        return DocumentUploadResponse(
            document_id=str(uuid.uuid4()),
            filename=file.filename,
            status="error",
            message=f"Error: {e.detail}"
        )
    except Exception as e:
        logger.error(f"❌ Error en upload de frontend: {e}")
        return DocumentUploadResponse(
            document_id=str(uuid.uuid4()),
            filename=file.filename,
            status="error",
            message=f"Error interno: {str(e)}"
        )

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