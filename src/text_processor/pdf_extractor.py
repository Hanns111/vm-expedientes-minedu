#!/usr/bin/env python
# -*- coding: utf-8 -*-
# src/text_processor/pdf_extractor.py

import os
import logging
import fitz  # PyMuPDF
import argparse
from pathlib import Path

# Intentar importar desde la ubicación correcta de settings
try:
    from config.settings import RAW_TEXT_INPUT_PATH, RAW_DATA_DIR
except ModuleNotFoundError:
    import sys
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
    sys.path.append(project_root)
    # Si no existe, definimos rutas por defecto
    RAW_DATA_DIR = os.path.join(project_root, 'data', 'raw')
    RAW_TEXT_INPUT_PATH = os.path.join(RAW_DATA_DIR, 'resultado.txt')

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path, output_path=None):
    """
    Extrae el texto de un archivo PDF y lo guarda en un archivo de texto.
    
    Args:
        pdf_path (str): Ruta al archivo PDF.
        output_path (str, optional): Ruta donde guardar el archivo de texto extraído.
                                    Si no se proporciona, se usará el mismo nombre del PDF
                                    pero con extensión .txt en el mismo directorio.
    
    Returns:
        str: Ruta al archivo de texto generado.
    """
    try:
        # Verificar que el archivo exista
        if not os.path.exists(pdf_path):
            logger.error(f"El archivo PDF no existe: {pdf_path}")
            return None
        
        # Si no se proporciona una ruta de salida, crear una basada en el nombre del PDF
        if output_path is None:
            pdf_name = os.path.basename(pdf_path)
            pdf_name_without_ext = os.path.splitext(pdf_name)[0]
            output_path = os.path.join(os.path.dirname(pdf_path), f"{pdf_name_without_ext}.txt")
        
        logger.info(f"Extrayendo texto de: {pdf_path}")
        logger.info(f"Guardando resultado en: {output_path}")
        
        # Abrir el PDF
        doc = fitz.open(pdf_path)
        text = ""
        
        # Extraer texto de cada página
        total_pages = len(doc)
        logger.info(f"El PDF tiene {total_pages} páginas")
        
        for page_num, page in enumerate(doc, 1):
            if page_num % 10 == 0 or page_num == 1 or page_num == total_pages:
                logger.info(f"Procesando página {page_num}/{total_pages}")
            
            # Extraer texto de la página
            page_text = page.get_text()
            text += page_text + "\n\n"  # Agregar separación entre páginas
        
        # Guardar el texto extraído
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        
        logger.info(f"✅ Extracción completada. Texto guardado en: {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error al extraer texto del PDF: {e}", exc_info=True)
        return None

def process_all_pdfs_in_directory(directory_path=None, output_dir=None):
    """
    Procesa todos los archivos PDF en un directorio y extrae su texto.
    
    Args:
        directory_path (str, optional): Directorio donde buscar archivos PDF.
                                       Si no se proporciona, se usará RAW_DATA_DIR.
        output_dir (str, optional): Directorio donde guardar los archivos de texto extraídos.
                                   Si no se proporciona, se usará el mismo directorio de entrada.
    
    Returns:
        list: Lista de rutas a los archivos de texto generados.
    """
    if directory_path is None:
        directory_path = RAW_DATA_DIR
    
    if output_dir is None:
        output_dir = directory_path
    
    # Asegurarse de que el directorio de salida exista
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Buscando archivos PDF en: {directory_path}")
    
    # Encontrar todos los archivos PDF en el directorio
    pdf_files = [f for f in os.listdir(directory_path) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        logger.warning(f"No se encontraron archivos PDF en: {directory_path}")
        return []
    
    logger.info(f"Se encontraron {len(pdf_files)} archivos PDF")
    
    # Procesar cada archivo PDF
    output_files = []
    for pdf_file in pdf_files:
        pdf_path = os.path.join(directory_path, pdf_file)
        pdf_name_without_ext = os.path.splitext(pdf_file)[0]
        output_path = os.path.join(output_dir, f"{pdf_name_without_ext}.txt")
        
        result_path = extract_text_from_pdf(pdf_path, output_path)
        if result_path:
            output_files.append(result_path)
    
    return output_files

def main():
    """Función principal para ejecutar el script desde la línea de comandos."""
    parser = argparse.ArgumentParser(description='Extrae texto de archivos PDF.')
    parser.add_argument('--pdf', help='Ruta al archivo PDF específico a procesar')
    parser.add_argument('--dir', help='Directorio donde buscar archivos PDF')
    parser.add_argument('--output', help='Ruta o directorio de salida para los archivos de texto')
    parser.add_argument('--all', action='store_true', help='Procesar todos los PDFs en el directorio RAW_DATA_DIR')
    
    args = parser.parse_args()
    
    if args.pdf:
        # Procesar un solo archivo PDF
        output_path = args.output if args.output else None
        extract_text_from_pdf(args.pdf, output_path)
    elif args.dir or args.all:
        # Procesar todos los PDFs en un directorio
        directory = args.dir if args.dir else RAW_DATA_DIR
        output_dir = args.output if args.output else directory
        process_all_pdfs_in_directory(directory, output_dir)
    else:
        # Si no se proporcionan argumentos, procesar todos los PDFs en RAW_DATA_DIR
        logger.info("No se proporcionaron argumentos específicos. Procesando todos los PDFs en el directorio de datos raw.")
        process_all_pdfs_in_directory()

if __name__ == "__main__":
    logger.info("Ejecutando pdf_extractor.py como script principal.")
    main()
