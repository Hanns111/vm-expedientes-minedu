# config/settings.py
from pathlib import Path
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env (si existe)
load_dotenv(encoding='utf-16')

# Ruta base del proyecto (asumiendo que settings.py está en config/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Rutas de datos
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
CATEGORIES_DATA_DIR = DATA_DIR / "categories" # Aunque esté vacía, es bueno definirla

# Rutas específicas de archivos procesados
VECTORSTORE_FILENAME = "vectorstore_consolidated.pkl" # Nombre unificado
CHUNKS_FILENAME = "chunks_consolidated.json" # Nombre unificado

VECTORSTORE_PATH = PROCESSED_DATA_DIR / VECTORSTORE_FILENAME
CHUNKS_PATH = PROCESSED_DATA_DIR / CHUNKS_FILENAME

# Configuraciones de IA (ejemplos, se pueden expandir)
# Por ejemplo, si usas un modelo específico de Spacy:
SPACY_MODEL_NAME = os.getenv("SPACY_MODEL_NAME", "es_core_news_lg") # Modelo por defecto si no está en .env

# Otras configuraciones
# Por ejemplo, la ruta a Tesseract si no está en el PATH
# TESSERACT_CMD_PATH = os.getenv("TESSERACT_CMD_PATH", None) # Descomentar y configurar si es necesario

# Puedes añadir más configuraciones aquí según sea necesario
# como umbrales, nombres de modelos, etc.

# Ruta para el archivo de texto crudo de entrada para preprocesamiento
RAW_TEXT_INPUT_FILENAME = "resultado.txt" # O el nombre de archivo que uses
RAW_TEXT_INPUT_PATH = RAW_DATA_DIR / RAW_TEXT_INPUT_FILENAME

# Para verificar que las rutas se construyen correctamente (opcional, para debugging)
if __name__ == "__main__":
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"DATA_DIR: {DATA_DIR}")
    print(f"RAW_DATA_DIR: {RAW_DATA_DIR}")
    print(f"PROCESSED_DATA_DIR: {PROCESSED_DATA_DIR}")
    print(f"VECTORSTORE_PATH: {VECTORSTORE_PATH}")
    print(f"CHUNKS_PATH: {CHUNKS_PATH}")
    print(f"SPACY_MODEL_NAME: {SPACY_MODEL_NAME}")
    print(f"RAW_TEXT_INPUT_PATH: {RAW_TEXT_INPUT_PATH}")
