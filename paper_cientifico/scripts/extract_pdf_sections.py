#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para extraer secciones específicas del PDF de la Directiva MINEDU.
"""

import os
import sys
import re
import json
import logging
import fitz  # PyMuPDF

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("extract_pdf_sections")

def extract_pdf_text(pdf_path):
    """Extrae todo el texto del PDF."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        logger.info(f"Texto extraído correctamente del PDF: {pdf_path}")
        return text
    except Exception as e:
        logger.error(f"Error al extraer texto del PDF: {e}")
        return None

def find_section(text, section_pattern):
    """Busca una sección específica en el texto."""
    match = re.search(section_pattern, text, re.DOTALL)
    if match:
        return match.group(0)
    return None

def extract_sections(text):
    """Extrae las secciones específicas mencionadas."""
    sections = {}
    
    # Patrones para cada sección
    section_patterns = {
        "procedimientos_emergencia": r"8\.3\.8[.\s\S]*?(?=8\.3\.9|8\.4)",
        "reprogramaciones": r"8\.5[.\s\S]*?(?=8\.6)",
        "reembolsos": r"8\.6[.\s\S]*?(?=8\.7)",
        "recuperacion_viaticos": r"8\.7[.\s\S]*?(?=8\.8|9\.)",
        "casos_especiales": r"8\.3\.10[.\s\S]*?(?=8\.3\.11|8\.4)",
        "responsabilidades": r"9\.[.\s\S]*?(?=10\.)",
        "disposiciones_complementarias": r"10\.[.\s\S]*?(?=11\.|ANEXO)",
        "rendicion_cuentas": r"8\.4\.[.\s\S]*?(?=8\.5)",
        "plazos_sanciones": r"(?:plazo|sanción|sancion)[.\s\S]*?(?=\n\n)",
        "montos_movilidad": r"8\.4\.17[.\s\S]*?(?=8\.4\.18)"
    }
    
    # Extraer cada sección
    for name, pattern in section_patterns.items():
        section_text = find_section(text, pattern)
        if section_text:
            sections[name] = section_text.strip()
            logger.info(f"Sección '{name}' encontrada: {len(section_text)} caracteres")
        else:
            logger.warning(f"Sección '{name}' no encontrada")
    
    return sections

def save_sections(sections, output_path):
    """Guarda las secciones extraídas en un archivo JSON."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sections, f, indent=2, ensure_ascii=False)
        logger.info(f"Secciones guardadas correctamente en {output_path}")
    except Exception as e:
        logger.error(f"Error al guardar secciones: {e}")

def main():
    # Definir rutas
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    pdf_path = os.path.join(base_dir, "data", "raw", "DIRECTIVA N° 011-2020-MINEDU_LIMPIA.pdf")
    output_dir = os.path.join(base_dir, "paper_cientifico", "dataset", "extracted_sections")
    output_path = os.path.join(output_dir, "directiva_sections.json")
    
    # Crear directorio de salida si no existe
    os.makedirs(output_dir, exist_ok=True)
    
    # Extraer texto del PDF
    text = extract_pdf_text(pdf_path)
    if not text:
        logger.error("No se pudo extraer texto del PDF")
        sys.exit(1)
    
    # Extraer secciones específicas
    sections = extract_sections(text)
    
    # Guardar secciones
    save_sections(sections, output_path)
    
    logger.info("Extracción de secciones completada con éxito")

if __name__ == "__main__":
    main()
