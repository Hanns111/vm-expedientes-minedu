import re

def extract_entities(text):
    """
    Extrae montos, fechas y numerales desde un texto.
    """
    # Buscar montos en formato S/. 100.00 o S/ 100
    montos = re.findall(r'S\/\.?\s*\d+(?:,\d{3})*(?:\.\d{2})?', text)

    # Buscar fechas en formato dd/mm/yyyy o dd-mm-yyyy
    fechas = re.findall(r'\b\d{2}[\/-]\d{2}[\/-]\d{4}\b', text)

    # Buscar numerales tipo 3.1, 5.2.4 o "Artículo 5"
    numerales = re.findall(r'\b\d+(\.\d+)+\b', text)
    articulos = re.findall(r'Artículo\s+\d+', text, re.IGNORECASE)

    return {
        "montos": montos,
        "fechas": fechas,
        "numerales": numerales + articulos
    }

# Ejemplo rápido de prueba
if __name__ == "__main__":
    ejemplo = """
    Según el numeral 5.2 de la Directiva, el monto máximo es S/. 320.00 por día.
    Esta disposición rige desde el 15/03/2024 según el Artículo 7.
    """
    print(extract_entities(ejemplo))
