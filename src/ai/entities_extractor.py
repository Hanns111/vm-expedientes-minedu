import re
import spacy
from dateutil import parser
import locale # Para el parseo de fechas en español

# Quitar la carga global de nlp aquí

class EntitiesExtractor:
    def __init__(self, model_name="es_core_news_sm"): # Aceptar model_name
        # Cargar el modelo de spaCy
        try:
            self.nlp = spacy.load(model_name)
            self.has_nlp = True
        except (IOError, ImportError):
            print(f"Advertencia: No se pudo cargar el modelo {model_name}. Las entidades nombradas no estarán disponibles.")
            self.has_nlp = False
            
        self.currency_patterns = [
            r'S/\.?\s*\d+(?:,\d{3})*(?:\.\d{2})?',  # S/. 100.00 o S/ 100
            r'S/\.?\s*\d+(?:\.\d{3})*(?:,\d{2})?',  # S/. 100,00 o S/ 100
            r'\d+(?:,\d{3})*(?:\.\d{2})?\s*S/\.?',   # 100.00 S/. o 100 S/
        ]
        
        self.date_patterns = [
            r'\b\d{2}[/-]\d{2}[/-]\d{4}\b',  # dd/mm/yyyy o dd-mm-yyyy
            r'\b\d{2}\s+de\s+[a-zA-ZáéíóúÁÉÍÓÚÑñ]+\s+de\s+\d{4}\b', # Modificado para incluir tildes y ñ
            r'\b\d{1,2}\s+[a-zA-ZáéíóúÁÉÍÓÚÑñ]+\s+\d{4}\b', # Modificado para incluir tildes y ñ
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
        """Extrae fechas en múltiples formatos y las normaliza."""
        dates_found_raw = []
        for pattern in self.date_patterns:
            dates_found_raw.extend(re.findall(pattern, text))
        
        # Intentar configurar el locale para español para dateutil.parser
        # Esto es importante para meses como "enero", "febrero", etc.
        current_locale = locale.getlocale(locale.LC_TIME)
        try:
            locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8') # o 'es_PE.UTF-8' si está disponible
        except locale.Error:
            try:
                locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252') # Windows
            except locale.Error:
                print("Advertencia: No se pudo establecer el locale a español para el parseo de fechas.")
        
        parsed_dates = []
        for date_str in dates_found_raw:
            try:
                date_obj = parser.parse(date_str, fuzzy=False) # fuzzy=False para ser más estricto
                parsed_dates.append(date_obj.strftime("%d/%m/%Y"))
            except (ValueError, TypeError):
                # Si falla el parseo estricto, se podría intentar con fuzzy o registrar el error
                # print(f"No se pudo parsear la fecha: {date_str}")
                parsed_dates.append(date_str) # Mantener la cadena original si no se puede parsear
        
        # Restaurar el locale original
        try:
            locale.setlocale(locale.LC_TIME, current_locale)
        except locale.Error:
            pass # No hacer nada si no se puede restaurar
            
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
        # Extraer entidades nombradas con spaCy si está disponible
        doc_ents_list = []
        if hasattr(self, 'has_nlp') and self.has_nlp:
            doc = self.nlp(text)
            # Modificar para que coincida con el formato esperado por SearchEngine
            for ent in doc.ents:
                doc_ents_list.append({"valor": ent.text, "tipo": ent.label_})
        else:
            print("Advertencia: Modelo NLP no disponible en EntitiesExtractor. No se extraerán entidades nombradas por Spacy.")

        entities = {
            "montos": self.extract_currency(text),
            "fechas": self.extract_dates(text),
            "numerales": self.extract_numerals(text),
            "porcentajes": self.extract_percentages(text),
            "expedientes": self.extract_expedientes(text),
            "entidades": doc_ents_list # Lista de diccionarios
        }
        
        # Agregar contexto a las entidades (excepto las de Spacy que ya tienen 'valor' y 'tipo')
        # El formato de las entidades de Spacy ya es una lista de dicts,
        # pero _add_context espera una lista de strings (values).
        # Por ahora, las entidades de Spacy no tendrán "contexto" adicional de _add_context.
        for key in entities:
            if key != "entidades": # No aplicar _add_context a las entidades de Spacy por ahora
                # _add_context espera una lista de strings, pero nuestras funciones de extracción ya devuelven strings
                entities[key] = self._add_context(text, entities[key]) 
        
        return entities

    def _add_context(self, text, values):
        """Agrega contexto a los valores encontrados (que son strings)"""
        results = []
        for value_str in values: # value_str es un string aquí
            # Encontrar la posición del valor en el texto
            try:
                # value_str debe ser un string para re.escape
                escaped_value = re.escape(str(value_str))
                # Buscar todas las ocurrencias para no tomar siempre la primera
                for match in re.finditer(escaped_value, text):
                    start = match.start()
                    end = match.end()
                    # Tomar N caracteres antes y después como contexto
                    context_start = max(0, start - 30) # Contexto más corto
                    context_end = min(len(text), end + 30)
                    
                    # Reconstruir el contexto con el valor original (no escapado)
                    # Asegurarse de que el valor original se resalte correctamente
                    pre_context = text[context_start:start]
                    post_context = text[end:context_end]
                    
                    context_highlighted = f"{pre_context}[{text[start:end]}]{post_context}"
                    
                    results.append({
                        "valor": text[start:end], # Usar el texto original del match
                        "contexto": context_highlighted.replace('\n', ' ').strip()
                    })
            except re.error: # En caso de que value_str sea problemático para re.escape
                 results.append({"valor": str(value_str), "contexto": str(value_str)}) # Fallback
            except Exception: # Captura general por si acaso
                 results.append({"valor": str(value_str), "contexto": str(value_str)})

        # Eliminar duplicados basados en valor y contexto para evitar redundancia
        unique_results = []
        seen = set()
        for res_dict in results:
            identifier = (res_dict['valor'], res_dict['contexto'])
            if identifier not in seen:
                unique_results.append(res_dict)
                seen.add(identifier)
        return unique_results

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
