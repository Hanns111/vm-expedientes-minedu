"""
Utilidades seguras para el uso de pickle con validación y verificación de integridad
"""
import pickle
import hashlib
from pathlib import Path
from typing import Any, Dict, Tuple, Optional
from src.core.security.file_validator import FileValidator
from src.core.security.input_validator import SecurityError

class SafePickleLoader:
    """Cargador seguro de archivos pickle con validación"""
    
    @staticmethod
    def load_with_validation(
        file_path: Path, 
        required_keys: Optional[list] = None,
        max_file_size_mb: int = 100
    ) -> Tuple[Any, str]:
        """
        Carga un archivo pickle de forma segura con validación completa
        
        Args:
            file_path: Ruta al archivo pickle
            required_keys: Lista de claves requeridas en el objeto cargado
            max_file_size_mb: Tamaño máximo del archivo en MB
            
        Returns:
            (objeto_cargado, hash_del_archivo)
            
        Raises:
            SecurityError: Si el archivo no es seguro o válido
        """
        # Validar archivo antes de cargar
        is_valid, error_msg = FileValidator.validate_file(file_path)
        if not is_valid:
            raise SecurityError(f"Archivo no válido: {error_msg}")
        
        # Verificar tamaño del archivo
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > max_file_size_mb:
            raise SecurityError(f"Archivo demasiado grande: {file_size_mb:.1f}MB (máximo: {max_file_size_mb}MB)")
        
        # Calcular hash para verificación de integridad
        file_hash = FileValidator.calculate_file_hash(file_path)
        
        try:
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
        except (pickle.UnpicklingError, EOFError, ValueError) as e:
            raise SecurityError(f"Error al deserializar pickle: {str(e)}")
        except Exception as e:
            raise SecurityError(f"Error inesperado al cargar pickle: {str(e)}")
        
        # Validar estructura si se especifican claves requeridas
        if required_keys and isinstance(data, dict):
            for key in required_keys:
                if key not in data:
                    raise SecurityError(f"Objeto inválido: falta la clave '{key}'")
        
        return data, file_hash
    
    @staticmethod
    def save_with_validation(
        data: Any, 
        file_path: Path,
        overwrite: bool = False
    ) -> str:
        """
        Guarda un objeto en formato pickle de forma segura
        
        Args:
            data: Objeto a guardar
            file_path: Ruta donde guardar el archivo
            overwrite: Si se permite sobrescribir archivos existentes
            
        Returns:
            Hash del archivo guardado
            
        Raises:
            SecurityError: Si hay problemas de seguridad
        """
        # Verificar si el archivo existe y si se permite sobrescribir
        if file_path.exists() and not overwrite:
            raise SecurityError(f"Archivo ya existe: {file_path}")
        
        # Validar que el directorio padre existe
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            raise SecurityError(f"Error al guardar pickle: {str(e)}")
        
        # Calcular y retornar hash del archivo guardado
        return FileValidator.calculate_file_hash(file_path)
    
    @staticmethod
    def validate_vectorstore_structure(data: Dict) -> bool:
        """
        Valida la estructura de un vectorstore
        
        Args:
            data: Datos del vectorstore
            
        Returns:
            True si la estructura es válida
            
        Raises:
            SecurityError: Si la estructura es inválida
        """
        if not isinstance(data, dict):
            raise SecurityError("Vectorstore debe ser un diccionario")
        
        # Verificar claves básicas
        basic_keys = ['chunks']
        for key in basic_keys:
            if key not in data:
                raise SecurityError(f"Vectorstore inválido: falta la clave '{key}'")
        
        # Verificar que chunks es una lista
        if not isinstance(data['chunks'], list):
            raise SecurityError("Vectorstore inválido: 'chunks' debe ser una lista")
        
        # Verificar que hay al menos un chunk
        if len(data['chunks']) == 0:
            raise SecurityError("Vectorstore inválido: no hay chunks")
        
        return True

def safe_load_vectorstore(vectorstore_path: Path) -> Tuple[Dict, str]:
    """
    Función de conveniencia para cargar vectorstores de forma segura
    
    Args:
        vectorstore_path: Ruta al archivo del vectorstore
        
    Returns:
        (vectorstore_data, file_hash)
    """
    # Claves requeridas para un vectorstore
    required_keys = ['chunks']
    
    data, file_hash = SafePickleLoader.load_with_validation(
        vectorstore_path, 
        required_keys=required_keys
    )
    
    # Validar estructura específica del vectorstore
    SafePickleLoader.validate_vectorstore_structure(data)
    
    return data, file_hash 