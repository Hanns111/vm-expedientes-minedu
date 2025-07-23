"""
Cargador dinámico de documentos normativos
Permite agregar nuevos documentos sin reiniciar el sistema
"""
import logging
import hashlib
from typing import Dict, Any, List, Optional, BinaryIO
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from enum import Enum
import json

# PDF processing
try:
    import PyPDF2
    import pdfplumber
    PDF_PROCESSING_AVAILABLE = True
except ImportError:
    PDF_PROCESSING_AVAILABLE = False

# Text processing
import re
from uuid import uuid4

logger = logging.getLogger(__name__)

class DocumentType(Enum):
    """Tipos de documento soportados"""
    PDF = "pdf"
    TXT = "txt"
    JSON = "json"
    DOCX = "docx"

class ProcessingStatus(Enum):
    """Estados de procesamiento"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class DocumentMetadata:
    """Metadatos de documento cargado"""
    document_id: str
    filename: str
    document_type: DocumentType
    file_size: int
    file_hash: str
    upload_date: datetime
    processed_date: Optional[datetime]
    status: ProcessingStatus
    norm_type: str  # "ley", "decreto", "directiva", etc.
    publication_date: Optional[datetime]
    validity_status: str  # "vigente", "derogada", "modificada"
    tags: List[str]
    user_uploaded: str
    chunks_generated: int
    processing_errors: List[str]

@dataclass 
class ProcessingResult:
    """Resultado del procesamiento de documento"""
    success: bool
    document_id: str
    chunks_created: int
    vectorstore_updated: bool
    processing_time: float
    errors: List[str]
    warnings: List[str]
    metadata: DocumentMetadata

class DynamicDocumentLoader:
    """
    Cargador dinámico de documentos normativos
    Permite cargar, procesar y integrar nuevos documentos en tiempo real
    """
    
    def __init__(self, 
                 upload_dir: Optional[Path] = None,
                 processed_dir: Optional[Path] = None,
                 allowed_extensions: Optional[List[str]] = None):
        
        self.upload_dir = upload_dir or Path(__file__).parent / "uploads"
        self.processed_dir = processed_dir or Path(__file__).parent / "processed"
        
        # Crear directorios
        self.upload_dir.mkdir(exist_ok=True)
        self.processed_dir.mkdir(exist_ok=True)
        
        # Extensiones permitidas
        self.allowed_extensions = allowed_extensions or ['.pdf', '.txt', '.json', '.docx']
        
        # Límites de seguridad
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.max_pages = 500  # Máximo páginas PDF
        
        # Base de datos de documentos (JSON simple)
        self.documents_db_path = self.processed_dir / "documents_db.json"
        self.documents_db = self._load_documents_db()
        
        logger.info(f"📁 DynamicDocumentLoader inicializado - Uploads: {self.upload_dir}")
    
    def upload_document(self,
                       file_data: BinaryIO,
                       filename: str,
                       metadata: Dict[str, Any],
                       user_id: str) -> ProcessingResult:
        """
        Cargar un nuevo documento normativo
        
        Args:
            file_data: Datos binarios del archivo
            filename: Nombre del archivo
            metadata: Metadatos del documento (tipo, fecha, etc.)
            user_id: ID del usuario que sube el archivo
        
        Returns:
            Resultado del procesamiento
        """
        start_time = datetime.now()
        
        try:
            # 1. Validaciones de seguridad
            validation_result = self._validate_upload(file_data, filename, metadata)
            if not validation_result["valid"]:
                return ProcessingResult(
                    success=False,
                    document_id="",
                    chunks_created=0,
                    vectorstore_updated=False,
                    processing_time=0.0,
                    errors=validation_result["errors"],
                    warnings=[],
                    metadata=None
                )
            
            # 2. Generar ID único y hash
            document_id = str(uuid4())
            file_content = file_data.read()
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # 3. Verificar duplicados
            if self._is_duplicate(file_hash):
                return ProcessingResult(
                    success=False,
                    document_id=document_id,
                    chunks_created=0,
                    vectorstore_updated=False,
                    processing_time=0.0,
                    errors=["Documento ya existe en el sistema"],
                    warnings=[],
                    metadata=None
                )
            
            # 4. Guardar archivo
            file_extension = Path(filename).suffix.lower()
            safe_filename = f"{document_id}_{self._sanitize_filename(filename)}"
            file_path = self.upload_dir / safe_filename
            
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # 5. Crear metadatos
            doc_metadata = DocumentMetadata(
                document_id=document_id,
                filename=filename,
                document_type=self._detect_document_type(file_extension),
                file_size=len(file_content),
                file_hash=file_hash,
                upload_date=datetime.now(),
                processed_date=None,
                status=ProcessingStatus.PENDING,
                norm_type=metadata.get("norm_type", "directiva"),
                publication_date=self._parse_date(metadata.get("publication_date")),
                validity_status=metadata.get("validity_status", "vigente"),
                tags=metadata.get("tags", []),
                user_uploaded=user_id,
                chunks_generated=0,
                processing_errors=[]
            )
            
            # 6. Procesar documento
            processing_result = self._process_document(file_path, doc_metadata)
            
            # 7. Actualizar base de datos
            self.documents_db[document_id] = doc_metadata.__dict__
            self._save_documents_db()
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return ProcessingResult(
                success=processing_result["success"],
                document_id=document_id,
                chunks_created=processing_result["chunks_created"],
                vectorstore_updated=processing_result["vectorstore_updated"],
                processing_time=processing_time,
                errors=processing_result["errors"],
                warnings=processing_result["warnings"],
                metadata=doc_metadata
            )
            
        except Exception as e:
            logger.error(f"❌ Error subiendo documento: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return ProcessingResult(
                success=False,
                document_id="",
                chunks_created=0,
                vectorstore_updated=False,
                processing_time=processing_time,
                errors=[str(e)],
                warnings=[],
                metadata=None
            )
    
    def _validate_upload(self, file_data: BinaryIO, filename: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validar archivo antes de procesamiento"""
        errors = []
        
        # Validar extensión
        file_extension = Path(filename).suffix.lower()
        if file_extension not in self.allowed_extensions:
            errors.append(f"Extensión no permitida: {file_extension}. Permitidas: {self.allowed_extensions}")
        
        # Validar tamaño
        file_data.seek(0, 2)  # Ir al final
        file_size = file_data.tell()
        file_data.seek(0)  # Volver al inicio
        
        if file_size > self.max_file_size:
            errors.append(f"Archivo muy grande: {file_size} bytes. Máximo: {self.max_file_size}")
        
        if file_size == 0:
            errors.append("Archivo vacío")
        
        # Validar metadatos requeridos
        required_fields = ["norm_type"]
        for field in required_fields:
            if field not in metadata or not metadata[field]:
                errors.append(f"Campo requerido faltante: {field}")
        
        # Validar nombre de archivo
        if not filename or len(filename) < 3:
            errors.append("Nombre de archivo inválido")
        
        # Verificar caracteres peligrosos en nombre
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        if any(char in filename for char in dangerous_chars):
            errors.append("Nombre de archivo contiene caracteres no permitidos")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _is_duplicate(self, file_hash: str) -> bool:
        """Verificar si el archivo ya existe"""
        for doc in self.documents_db.values():
            if isinstance(doc, dict) and doc.get("file_hash") == file_hash:
                return True
        return False
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitizar nombre de archivo"""
        # Eliminar caracteres peligrosos
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Limitar longitud
        if len(sanitized) > 100:
            name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
            sanitized = name[:90] + ('.' + ext if ext else '')
        
        return sanitized
    
    def _detect_document_type(self, file_extension: str) -> DocumentType:
        """Detectar tipo de documento por extensión"""
        type_mapping = {
            '.pdf': DocumentType.PDF,
            '.txt': DocumentType.TXT,
            '.json': DocumentType.JSON,
            '.docx': DocumentType.DOCX
        }
        return type_mapping.get(file_extension.lower(), DocumentType.TXT)
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parsear fecha de string"""
        if not date_str:
            return None
        
        try:
            # Intentar diferentes formatos
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            return None
        except Exception:
            return None
    
    def _process_document(self, file_path: Path, metadata: DocumentMetadata) -> Dict[str, Any]:
        """Procesar documento y generar chunks"""
        try:
            metadata.status = ProcessingStatus.PROCESSING
            
            # Extraer texto según tipo
            if metadata.document_type == DocumentType.PDF:
                text_content = self._extract_pdf_text(file_path)
            elif metadata.document_type == DocumentType.TXT:
                text_content = self._extract_txt_text(file_path)
            elif metadata.document_type == DocumentType.JSON:
                text_content = self._extract_json_text(file_path)
            else:
                return {
                    "success": False,
                    "chunks_created": 0,
                    "vectorstore_updated": False,
                    "errors": [f"Tipo de documento no soportado: {metadata.document_type}"],
                    "warnings": []
                }
            
            if not text_content:
                return {
                    "success": False,
                    "chunks_created": 0,
                    "vectorstore_updated": False,
                    "errors": ["No se pudo extraer texto del documento"],
                    "warnings": []
                }
            
            # Generar chunks
            chunks = self._generate_chunks(text_content, metadata)
            
            # Guardar chunks
            chunks_file = self.processed_dir / f"{metadata.document_id}_chunks.json"
            with open(chunks_file, 'w', encoding='utf-8') as f:
                json.dump(chunks, f, ensure_ascii=False, indent=2)
            
            # Actualizar metadatos
            metadata.chunks_generated = len(chunks)
            metadata.processed_date = datetime.now()
            metadata.status = ProcessingStatus.COMPLETED
            
            # TODO: Actualizar vectorstores
            vectorstore_updated = self._update_vectorstores(chunks, metadata)
            
            return {
                "success": True,
                "chunks_created": len(chunks),
                "vectorstore_updated": vectorstore_updated,
                "errors": [],
                "warnings": []
            }
            
        except Exception as e:
            logger.error(f"❌ Error procesando documento: {e}")
            metadata.status = ProcessingStatus.FAILED
            metadata.processing_errors.append(str(e))
            
            return {
                "success": False,
                "chunks_created": 0,
                "vectorstore_updated": False,
                "errors": [str(e)],
                "warnings": []
            }
    
    def _extract_pdf_text(self, file_path: Path) -> str:
        """Extraer texto de PDF"""
        if not PDF_PROCESSING_AVAILABLE:
            raise ImportError("PyPDF2 o pdfplumber no disponibles")
        
        text_content = ""
        
        try:
            # Intentar con pdfplumber primero (mejor para texto)
            with pdfplumber.open(file_path) as pdf:
                if len(pdf.pages) > self.max_pages:
                    raise ValueError(f"PDF muy largo: {len(pdf.pages)} páginas. Máximo: {self.max_pages}")
                
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"
        
        except Exception as e:
            logger.warning(f"pdfplumber falló, intentando PyPDF2: {e}")
            
            # Fallback con PyPDF2
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    
                    if len(pdf_reader.pages) > self.max_pages:
                        raise ValueError(f"PDF muy largo: {len(pdf_reader.pages)} páginas")
                    
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_content += page_text + "\n"
            
            except Exception as e2:
                raise Exception(f"No se pudo extraer texto del PDF: {e2}")
        
        return text_content.strip()
    
    def _extract_txt_text(self, file_path: Path) -> str:
        """Extraer texto de archivo TXT"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Intentar con otras codificaciones
            for encoding in ['latin-1', 'cp1252']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except:
                    continue
            raise Exception("No se pudo decodificar el archivo de texto")
    
    def _extract_json_text(self, file_path: Path) -> str:
        """Extraer texto de archivo JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extraer todo el texto del JSON
            def extract_text_from_json(obj):
                if isinstance(obj, str):
                    return obj + " "
                elif isinstance(obj, dict):
                    return " ".join(extract_text_from_json(v) for v in obj.values())
                elif isinstance(obj, list):
                    return " ".join(extract_text_from_json(item) for item in obj)
                else:
                    return str(obj) + " "
            
            return extract_text_from_json(data)
        
        except Exception as e:
            raise Exception(f"No se pudo procesar archivo JSON: {e}")
    
    def _generate_chunks(self, text: str, metadata: DocumentMetadata) -> List[Dict[str, Any]]:
        """Generar chunks del texto extraído"""
        # Configuración de chunking
        chunk_size = 1000
        chunk_overlap = 200
        
        # Limpiar texto
        cleaned_text = self._clean_text(text)
        
        # Dividir en chunks
        chunks = []
        text_length = len(cleaned_text)
        
        for i in range(0, text_length, chunk_size - chunk_overlap):
            chunk_text = cleaned_text[i:i + chunk_size]
            
            if len(chunk_text.strip()) < 50:  # Skip chunks muy pequeños
                continue
            
            chunk = {
                "id": f"{metadata.document_id}_chunk_{len(chunks)}",
                "document_id": metadata.document_id,
                "content": chunk_text.strip(),
                "chunk_index": len(chunks),
                "source": metadata.filename,
                "norm_type": metadata.norm_type,
                "publication_date": metadata.publication_date.isoformat() if metadata.publication_date else None,
                "validity_status": metadata.validity_status,
                "tags": metadata.tags,
                "created_date": datetime.now().isoformat()
            }
            chunks.append(chunk)
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Limpiar texto extraído"""
        # Eliminar caracteres de control
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Normalizar espacios
        text = re.sub(r'\s+', ' ', text)
        
        # Eliminar líneas muy cortas que suelen ser ruido
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if len(line) > 10:  # Solo líneas con contenido sustancial
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _update_vectorstores(self, chunks: List[Dict[str, Any]], metadata: DocumentMetadata) -> bool:
        """Actualizar vectorstores con nuevos chunks"""
        try:
            # Sistema Antialucinaciones v2.0.0: PROHIBIDO simular actualizaciones
            # TODO: Implementar actualización REAL de vectorstores con BM25/TFIDF
            
            logger.error(f"❌ CRÍTICO: Actualización real de vectorstores no implementada")
            logger.warning(f"⚠️ FALLA SEGURA: No se actualizarán vectorstores hasta implementación real")
            return False  # Falla segura - mejor admitir que no se implementó
            
            # Aquí se integraría con:
            # - BM25Retriever.add_documents(chunks)
            # - TFIDFRetriever.add_documents(chunks) 
            # - TransformerRetriever.add_documents(chunks)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error actualizando vectorstores: {e}")
            return False
    
    def _load_documents_db(self) -> Dict[str, Any]:
        """Cargar base de datos de documentos"""
        if self.documents_db_path.exists():
            try:
                with open(self.documents_db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error cargando DB de documentos: {e}")
        
        return {}
    
    def _save_documents_db(self):
        """Guardar base de datos de documentos"""
        try:
            # Convertir datetime a string para JSON
            serializable_db = {}
            for doc_id, doc_data in self.documents_db.items():
                if isinstance(doc_data, dict):
                    serializable_doc = doc_data.copy()
                    
                    # Convertir datetime fields
                    for field in ['upload_date', 'processed_date', 'publication_date']:
                        if field in serializable_doc and serializable_doc[field]:
                            if isinstance(serializable_doc[field], datetime):
                                serializable_doc[field] = serializable_doc[field].isoformat()
                    
                    # Convertir enums
                    if 'status' in serializable_doc:
                        if hasattr(serializable_doc['status'], 'value'):
                            serializable_doc['status'] = serializable_doc['status'].value
                    
                    if 'document_type' in serializable_doc:
                        if hasattr(serializable_doc['document_type'], 'value'):
                            serializable_doc['document_type'] = serializable_doc['document_type'].value
                    
                    serializable_db[doc_id] = serializable_doc
            
            with open(self.documents_db_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_db, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Error guardando DB de documentos: {e}")
    
    def list_documents(self, status: Optional[ProcessingStatus] = None) -> List[Dict[str, Any]]:
        """Listar documentos cargados"""
        documents = []
        
        for doc_id, doc_data in self.documents_db.items():
            if isinstance(doc_data, dict):
                if status is None or doc_data.get('status') == status.value:
                    documents.append({
                        "document_id": doc_id,
                        **doc_data
                    })
        
        # Ordenar por fecha de subida
        documents.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
        return documents
    
    def get_document_info(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Obtener información de un documento específico"""
        doc_data = self.documents_db.get(document_id)
        if doc_data:
            return {
                "document_id": document_id,
                **doc_data
            }
        return None
    
    def delete_document(self, document_id: str, user_id: str) -> bool:
        """Eliminar documento (solo admin)"""
        try:
            if document_id not in self.documents_db:
                return False
            
            doc_data = self.documents_db[document_id]
            
            # Eliminar archivos físicos
            filename = doc_data.get('filename', '')
            safe_filename = f"{document_id}_{self._sanitize_filename(filename)}"
            
            upload_file = self.upload_dir / safe_filename
            chunks_file = self.processed_dir / f"{document_id}_chunks.json"
            
            if upload_file.exists():
                upload_file.unlink()
            
            if chunks_file.exists():
                chunks_file.unlink()
            
            # Eliminar de DB
            del self.documents_db[document_id]
            self._save_documents_db()
            
            logger.info(f"🗑️ Documento eliminado: {document_id} por usuario {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error eliminando documento: {e}")
            return False
    
    def get_loader_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cargador"""
        total_docs = len(self.documents_db)
        
        status_counts = {}
        type_counts = {}
        total_chunks = 0
        
        for doc_data in self.documents_db.values():
            if isinstance(doc_data, dict):
                status = doc_data.get('status', 'unknown')
                doc_type = doc_data.get('document_type', 'unknown')
                
                status_counts[status] = status_counts.get(status, 0) + 1
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
                total_chunks += doc_data.get('chunks_generated', 0)
        
        return {
            "total_documents": total_docs,
            "total_chunks_generated": total_chunks,
            "status_distribution": status_counts,
            "type_distribution": type_counts,
            "upload_directory": str(self.upload_dir),
            "processed_directory": str(self.processed_dir),
            "max_file_size_mb": self.max_file_size / (1024 * 1024),
            "allowed_extensions": self.allowed_extensions,
            "pdf_processing_available": PDF_PROCESSING_AVAILABLE
        }

# Instancia global
global_document_loader = DynamicDocumentLoader()