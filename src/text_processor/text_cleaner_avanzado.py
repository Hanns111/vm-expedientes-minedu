import re
import unicodedata
import json
import os

# Rutas de archivos
ruta_chunks_original = "data/processed/chunks_v2.json"
ruta_chunks_limpios = "data/processed/chunks_limpios.json"
ruta_vectorstore = "data/processed/vectorstore_semantic_full_v2.pkl"
ruta_vectorstore_limpio = "data/processed/vectorstore_semantic_full_limpio.pkl"

def normalizar_texto(texto):
    """
    Normaliza el texto eliminando caracteres extraños y normalizando acentos.
    """
    # Normalizar caracteres Unicode (NFD -> NFC)
    texto = unicodedata.normalize('NFC', texto)
    
    # Eliminar caracteres no imprimibles
    texto = re.sub(r'[^\x20-\x7E\náéíóúÁÉÍÓÚñÑ°•]', ' ', texto)
    
    return texto

def corregir_espacios(texto):
    """
    Corrige espacios innecesarios entre caracteres y palabras.
    """
    # Corregir patrones comunes de OCR defectuoso
    
    # 1. Corregir palabras con espacios entre letras (p a l a b r a -> palabra)
    palabras_comunes = [
        'ministerio', 'educacion', 'directiva', 'procedimiento', 'administrativo',
        'documento', 'normativo', 'viaticos', 'pasajes', 'comision', 'servicio',
        'nacional', 'general', 'oficina', 'administracion', 'contabilidad',
        'presupuesto', 'tesoreria', 'coordinacion', 'financiera', 'control',
        'previo', 'abastecimiento', 'unidad', 'ejecutora', 'organica', 'fecha',
        'publicacion', 'emision', 'vigencia', 'aprobacion', 'resolucion'
    ]
    
    # Crear patrones para cada palabra común
    for palabra in palabras_comunes:
        # Crear un patrón que detecte la palabra con espacios entre letras
        patron = ''
        for letra in palabra:
            patron += letra + '\\s*'
        patron = patron.rstrip('\\s*')  # Quitar el último \s*
        
        # Reemplazar el patrón con la palabra correcta
        texto = re.sub(patron, palabra, texto, flags=re.IGNORECASE)
    
    # 2. Corregir patrones específicos
    patrones_especificos = [
        # Corregir "M I N E D U" -> "MINEDU"
        (r'M\s*I\s*N\s*E\s*D\s*U', 'MINEDU'),
        # Corregir "D\s*I\s*-\s*0\s*0\s*3" -> "DI-003"
        (r'D\s*I\s*-\s*0\s*0\s*3', 'DI-003'),
        # Corregir fechas con espacios
        (r'(\d+)\s*/\s*(\d+)\s*/\s*(\d+)', r'\1/\2/\3'),
        # Corregir números con espacios
        (r'(\d+)\s+(\.\s*\d+)', r'\1\2'),
    ]
    
    for patron, reemplazo in patrones_especificos:
        texto = re.sub(patron, reemplazo, texto)
    
    # 3. Eliminar espacios antes de puntuación
    texto = re.sub(r'\s+([.,;:?!)])', r'\1', texto)
    
    # 4. Eliminar espacios después de paréntesis de apertura
    texto = re.sub(r'[(]\s+', r'(', texto)
    
    # 5. Reemplazar múltiples espacios por uno solo
    texto = re.sub(r'\s+', ' ', texto)
    
    return texto

def corregir_errores_ocr(texto):
    """
    Corrige errores comunes de OCR.
    """
    # Corregir patrones específicos de OCR
    reemplazos = [
        # Corregir "l" por "i" en ciertos contextos
        (r'd\s*[eE]\s*l\s*', 'del '),
        (r'[eE]\s*l\s+', 'el '),
        
        # Corregir números y letras confundidos
        (r'0(?=[a-zA-Z])', 'o'),  # 0 seguido de letra probablemente es "o"
        (r'l(?=\d)', '1'),        # l seguido de número probablemente es "1"
        
        # Corregir palabras comunes mal OCR
        (r'd\s*[i1]rect[i1]va', 'directiva'),
        (r'm\s*[i1]n\s*[i1]ster[i1]o', 'ministerio'),
        (r'[eE]ducac[i1][o0]n', 'Educación'),
        (r'publ[i1]cac[i1][o0]n', 'publicación'),
        (r'[fF][eE][cC][hH][aA]', 'fecha'),
        
        # Corregir patrones de fechas
        (r'(\d+)[/\\](\d+)[/\\](\d+)', r'\1/\2/\3'),  # Normalizar separadores de fecha
    ]
    
    for patron, reemplazo in reemplazos:
        texto = re.sub(patron, reemplazo, texto)
    
    return texto

def limpiar_texto_avanzado(texto):
    """
    Aplica todas las técnicas de limpieza al texto.
    """
    # Normalizar el texto
    texto = normalizar_texto(texto)
    
    # Corregir errores de OCR
    texto = corregir_errores_ocr(texto)
    
    # Corregir espacios
    texto = corregir_espacios(texto)
    
    # Eliminar líneas vacías múltiples
    texto = re.sub(r'\n\s*\n', '\n\n', texto)
    
    return texto.strip()

def limpiar_chunks():
    """
    Limpia los chunks existentes y crea una nueva versión mejorada.
    """
    # Verificar si existe el archivo de chunks
    if not os.path.exists(ruta_chunks_original):
        print(f"No se encontro el archivo de chunks: {ruta_chunks_original}")
        return False
    
    # Cargar los chunks originales
    with open(ruta_chunks_original, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    # Limpiar cada chunk
    chunks_limpios = []
    for chunk in chunks:
        chunk_limpio = {
            "titulo": limpiar_texto_avanzado(chunk.get("titulo", "")),
            "texto": limpiar_texto_avanzado(chunk.get("texto", ""))
        }
        chunks_limpios.append(chunk_limpio)
    
    # Guardar los chunks limpios
    with open(ruta_chunks_limpios, 'w', encoding='utf-8') as f:
        json.dump(chunks_limpios, f, ensure_ascii=False, indent=2)
    
    print(f"Chunks limpios guardados en: {ruta_chunks_limpios}")
    return True

def limpiar_vectorstore():
    """
    Limpia el vectorstore existente y crea una nueva versión mejorada.
    """
    try:
        import pickle
        
        # Verificar si existe el archivo de vectorstore
        if not os.path.exists(ruta_vectorstore):
            print(f"No se encontro el archivo de vectorstore: {ruta_vectorstore}")
            return False
        
        # Cargar el vectorstore original
        with open(ruta_vectorstore, 'rb') as f:
            vectorstore = pickle.load(f)
        
        # Limpiar los chunks del vectorstore
        chunks_originales = vectorstore['chunks']
        chunks_limpios = []
        
        for chunk in chunks_originales:
            if isinstance(chunk, dict):
                chunk_limpio = {
                    "titulo": limpiar_texto_avanzado(chunk.get("titulo", "")),
                    "texto": limpiar_texto_avanzado(chunk.get("texto", ""))
                }
                chunks_limpios.append(chunk_limpio)
            else:
                # Si el chunk no es un diccionario, limpiarlo como texto
                chunks_limpios.append(limpiar_texto_avanzado(chunk))
        
        # Reemplazar los chunks en el vectorstore
        vectorstore['chunks'] = chunks_limpios
        
        # Guardar el vectorstore limpio
        with open(ruta_vectorstore_limpio, 'wb') as f:
            pickle.dump(vectorstore, f)
        
        print(f"Vectorstore limpio guardado en: {ruta_vectorstore_limpio}")
        return True
    
    except Exception as e:
        print(f"Error al limpiar el vectorstore: {str(e)}")
        return False

def mostrar_ejemplos_limpieza():
    """
    Muestra ejemplos de la limpieza para verificar su efectividad.
    """
    try:
        import pickle
        
        # Cargar el vectorstore original
        with open(ruta_vectorstore, 'rb') as f:
            vectorstore_original = pickle.load(f)
        
        # Cargar el vectorstore limpio
        with open(ruta_vectorstore_limpio, 'rb') as f:
            vectorstore_limpio = pickle.load(f)
        
        # Mostrar ejemplos de limpieza
        print("\n=== EJEMPLOS DE LIMPIEZA ===")
        
        for i in range(min(5, len(vectorstore_original['chunks']))):
            chunk_original = vectorstore_original['chunks'][i]
            chunk_limpio = vectorstore_limpio['chunks'][i]
            
            if isinstance(chunk_original, dict) and isinstance(chunk_limpio, dict):
                texto_original = chunk_original.get("texto", "")
                texto_limpio = chunk_limpio.get("texto", "")
            else:
                texto_original = chunk_original
                texto_limpio = chunk_limpio
            
            print(f"\n--- Ejemplo {i+1} ---")
            print("ORIGINAL:")
            print(texto_original[:200] + "..." if len(texto_original) > 200 else texto_original)
            print("\nLIMPIO:")
            print(texto_limpio[:200] + "..." if len(texto_limpio) > 200 else texto_limpio)
    
    except Exception as e:
        print(f"Error al mostrar ejemplos: {str(e)}")

if __name__ == "__main__":
    print("Iniciando limpieza avanzada de texto...")
    
    # Limpiar los chunks
    if limpiar_chunks():
        print("Limpieza de chunks completada.")
    
    # Limpiar el vectorstore
    if limpiar_vectorstore():
        print("Limpieza de vectorstore completada.")
        
        # Mostrar ejemplos de limpieza
        mostrar_ejemplos_limpieza()
    
    print("Proceso de limpieza finalizado.")
