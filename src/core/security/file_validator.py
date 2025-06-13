"""
Validador de archivos para prevenir malware y archivos maliciosos
"""
import hashlib
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
from src.core.config.security_config import SecurityConfig
from src.core.security.input_validator import SecurityError

class FileValidator:
    """Validador de archivos para prevenir malware y archivos maliciosos"""
    
    @staticmethod
    def validate_file(file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Valida que un archivo sea seguro para procesar
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            (es_valido, mensaje_error)
        """
        if not file_path.exists():
            return False, "El archivo no existe"
        
        # Verificar tamaño
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > SecurityConfig.MAX_FILE_SIZE_MB:
            return False, f"Archivo demasiado grande: {file_size_mb:.1f}MB (máximo: {SecurityConfig.MAX_FILE_SIZE_MB}MB)"
        
        # Verificar extensión
        if file_path.suffix.lower() not in SecurityConfig.ALLOWED_FILE_EXTENSIONS:
            return False, f"Extensión no permitida: {file_path.suffix}"
        
        # Verificar MIME type real (si python-magic está disponible)
        try:
            import magic
            file_mime = magic.from_file(str(file_path), mime=True)
            if file_mime not in SecurityConfig.ALLOWED_MIME_TYPES:
                return False, f"Tipo de archivo no permitido: {file_mime}"
        except ImportError:
            # Si python-magic no está disponible, solo verificar extensión
            pass
        except Exception as e:
            return False, f"Error verificando tipo de archivo: {str(e)}"
        
        # Verificaciones específicas por tipo
        if file_path.suffix.lower() == '.pdf':
            is_safe, error = FileValidator._validate_pdf(file_path)
            if not is_safe:
                return False, error
        
        return True, None
    
    @staticmethod
    def _validate_pdf(file_path: Path) -> Tuple[bool, Optional[str]]:
        """Validación específica para PDFs"""
        try:
            with open(file_path, 'rb') as f:
                # Leer primeros bytes para verificación rápida
                header = f.read(1024)
                
                # Verificar header PDF
                if not header.startswith(b'%PDF'):
                    return False, "No es un PDF válido"
                
                # Buscar JavaScript embebido (común en PDFs maliciosos)
                f.seek(0)
                content = f.read()
                
                dangerous_patterns = [
                    b'/JavaScript',
                    b'/JS',
                    b'/Launch',
                    b'/EmbeddedFile',
                    b'/OpenAction',
                    b'/AA',  # Additional Actions
                    b'/RichMedia'  # Flash content
                ]
                
                for pattern in dangerous_patterns:
                    if pattern in content:
                        return False, f"PDF contiene contenido potencialmente peligroso: {pattern.decode()}"
                
                return True, None
                
        except Exception as e:
            return False, f"Error al validar PDF: {str(e)}"
    
    @staticmethod
    def calculate_file_hash(file_path: Path, algorithm='sha256') -> str:
        """
        Calcula el hash de un archivo para verificación de integridad
        
        Args:
            file_path: Ruta al archivo
            algorithm: Algoritmo de hash ('sha256', 'md5')
            
        Returns:
            Hash del archivo
        """
        hash_func = hashlib.sha256() if algorithm == 'sha256' else hashlib.md5()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    @staticmethod
    def create_file_fingerprint(file_path: Path) -> Dict[str, Any]:
        """Crea una huella digital del archivo para auditoría"""
        return {
            'filename': file_path.name,
            'size_bytes': file_path.stat().st_size,
            'sha256': FileValidator.calculate_file_hash(file_path),
            'created_at': datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
            'modified_at': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        }
    
    @staticmethod
    def validate_file_path(file_path: str) -> bool:
        """
        Valida que una ruta de archivo sea segura
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            True si la ruta es segura
        """
        # Prevenir path traversal
        if '..' in file_path or '//' in file_path:
            return False
        
        # Verificar que esté dentro del directorio del proyecto
        try:
            resolved_path = Path(file_path).resolve()
            base_path = SecurityConfig.BASE_DIR.resolve()
            
            if not str(resolved_path).startswith(str(base_path)):
                return False
        except:
            return False
        
        return True
    
    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """
        Genera un nombre de archivo seguro
        
        Args:
            filename: Nombre original del archivo
            
        Returns:
            Nombre de archivo sanitizado
        """
        import re
        
        # Remover caracteres peligrosos
        safe_name = re.sub(r'[^\w\-. ]', '', filename)
        
        # Limitar longitud
        if len(safe_name) > 100:
            name, ext = safe_name.rsplit('.', 1) if '.' in safe_name else (safe_name, '')
            safe_name = name[:95] + '.' + ext if ext else name[:100]
        
        return safe_name 