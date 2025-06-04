import re
import spacy
from dateutil import parser

# Inicializar el modelo de spaCy para español
try:
    nlp = spacy.load("es_core_news_sm")
except Exception as e:
    print(f"\nError al cargar el modelo de spaCy: {e}")
    print("Por favor, instale el modelo usando: python -m spacy download es_core_news_sm")
    exit(1)

class EntitiesExtractor:
    def __init__(self):
        self.currency_patterns = [
            r'S/\.?\s*\d+(?:,\d{3})*(?:\.\d{2})?',  # S/. 100.00 o S/ 100
            r'S/\.?\s*\d+(?:\.\d{3})*(?:,\d{2})?',  # S/. 100,00 o S/ 100
            r'\d+(?:,\d{3})*(?:\.\d{2})?\s*S/\.?',   # 100.00 S/. o 100 S/
        ]
        
        self.date_patterns = [
            r'\b\d{2}[/-]\d{2}[/-]\d{4}\b',  # dd/mm/yyyy o dd-mm-yyyy
            r'\b\d{2}\s+de\s+[a-zA-Z]+\s+de\s+\d{4}\b',  # 15 de marzo de 2024
            r'\b\d{1,2}\s+[a-zA-Z]+\s+\d{4}\b',  # 15 marzo 2024
        ]
        
        self.numeral_patterns = [
            r'\b\d+(?:\.\d+)+\b',  # 5.2.4
            r'Art[íi]culo\s+\d+',    # Artículo 7
            r'Numeral\s+\d+(?:\.\d+)*',  # Numeral 5.2
            r'Párrafo\s+\d+',        # Párrafo 3
        ]
        
        self.percentage_patterns = [
            r'\d+(?:,\d+)?%?',  # 10% o 10
            r'\d+(?:\.\d+)?%?',  # 10.5% o 10.5
        ]
        
        self.expediente_patterns = [
            r'\bEXPEDIENTE\s+\d+-\d+\b',  # EXPEDIENTE 123-2024
            r'\bEXP\s+\d+-\d+\b',        # EXP 123-2024
        ]

    def extract_currency(self, text):
        """Extrae montos en soles con múltiples formatos"""
        amounts = []
        for pattern in self.currency_patterns:
            amounts.extend(re.findall(pattern, text))
        
        # Normalizar los montos (reemplazar comas por puntos)
        normalized = []
        for amount in amounts:
            # Si tiene S/. al inicio, lo mantenemos
            prefix = "S/. " if amount.startswith("S/") else ""
            # Normalizar el número
            number = amount.replace("S/", "").strip()
            number = number.replace(",", ".") if "." in number else number.replace(",", "")
            normalized.append(f"{prefix}{number}")
        
        return normalized

    def extract_dates(self, text):
        """Extrae fechas en múltiples formatos"""
        dates = []
        for pattern in self.date_patterns:
            dates.extend(re.findall(pattern, text))
        
        # Intentar parsear fechas en español
        try:
            locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        except:
            pass
        
        parsed_dates = []
        for date_str in dates:
            try:
                # Intentar parsear la fecha
                date_obj = parser.parse(date_str, fuzzy=True)
                # Formatear en formato estándar
                parsed_dates.append(date_obj.strftime("%d/%m/%Y"))
            except:
                continue
        
        return parsed_dates

    def extract_numerals(self, text):
        """Extrae numerales, artículos y párrafos"""
        numerals = []
        for pattern in self.numeral_patterns:
            numerals.extend(re.findall(pattern, text, re.IGNORECASE))
        return numerals

    def extract_percentages(self, text):
        """Extrae porcentajes"""
        percentages = []
        for pattern in self.percentage_patterns:
            percentages.extend(re.findall(pattern, text))
        return percentages

    def extract_expedientes(self, text):
        """Extrae números de expediente"""
        expedientes = []
        for pattern in self.expediente_patterns:
            expedientes.extend(re.findall(pattern, text))
        return expedientes

    def extract_entities(self, text):
        """Extrae todas las entidades importantes del texto"""
        # Procesar con spaCy para obtener entidades nombradas
        doc = nlp(text)
        
        # Extraer todas las entidades
        entities = {
            "montos": self.extract_currency(text),
            "fechas": self.extract_dates(text),
            "numerales": self.extract_numerals(text),
            "porcentajes": self.extract_percentages(text),
            "expedientes": self.extract_expedientes(text),
            "entidades": [ent.text for ent in doc.ents]
        }
        
        # Agregar contexto a las entidades
        for key in entities:
            if key != "entidades":
                entities[key] = self._add_context(text, entities[key])
        
        return entities

    def _add_context(self, text, values):
        """Agrega contexto a los valores encontrados"""
        results = []
        for value in values:
            # Encontrar la posición del valor en el texto
            start = text.find(value)
            if start != -1:
                # Tomar 50 caracteres antes y después como contexto
                context_start = max(0, start - 50)
                context_end = min(len(text), start + len(value) + 50)
                context = text[context_start:start] + "[" + value + "]" + text[start+len(value):context_end]
                results.append({
                    "valor": value,
                    "contexto": context.strip()
                })
        return results

# Ejemplo de uso
def main():
    extractor = EntitiesExtractor()
    
    ejemplo = """
    Según el numeral 5.2 de la Directiva, el monto máximo es S/. 320,00 por día.
    Esta disposición rige desde el 15 de marzo de 2024 según el Artículo 7.
    Los gastos no deben superar el 15% del presupuesto.
    EXPEDIENTE 123-2024
    """
    
    print("\n=== Extracción de Entidades ===")
    print(extractor.extract_entities(ejemplo))

if __name__ == "__main__":
    main()
