import pickle
import re
from entities_extractor import EntitiesExtractor

# Cargar el vectorstore
with open('data/processed/vectorstore_semantic_full_v2.pkl', 'rb') as f:
    vectorstore = pickle.load(f)

chunks = vectorstore['chunks']

# Palabras clave para buscar
palabras_clave = ['fecha', 'publicación', 'emisión', 'vigencia', 'aprobación', 'promulgación', 'directiva', 'aprob', 'emiti', 'publica', 'vigente', 'documento', 'normativo', 'resolución']

# Buscar chunks relevantes
chunks_relevantes = []
for i, chunk in enumerate(chunks):
    texto = chunk['texto'].lower()
    if any(palabra in texto for palabra in palabras_clave):
        chunks_relevantes.append((i, chunk))

print(f"\nSe encontraron {len(chunks_relevantes)} chunks relevantes.")

# Inicializar el extractor de entidades
extractor = EntitiesExtractor()

# Patrones adicionales para fechas
patrones_fecha = [
    r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',  # dd/mm/yy o dd/mm/yyyy
    r'\b\d{1,2}\s+de\s+[a-zA-Z]+\s+(?:de\s+)?\d{2,4}\b',  # dd de mes (de) yyyy
    r'\b[a-zA-Z]+\s+(?:de\s+)?\d{2,4}\b',  # mes (de) yyyy
    r'\b\d{2,4}\b'  # yyyy (año solo)
]

# Buscar fechas en los chunks relevantes
resultados = []
for i, chunk in chunks_relevantes:
    # Usar el extractor de entidades
    entidades = extractor.extract_entities(chunk['texto'])
    fechas_encontradas = entidades['fechas']
    
    # Buscar fechas con patrones adicionales
    texto = chunk['texto']
    for patron in patrones_fecha:
        matches = re.finditer(patron, texto)
        for match in matches:
            fecha_str = match.group(0)
            # Obtener contexto
            start = max(0, match.start() - 50)
            end = min(len(texto), match.end() + 50)
            contexto = texto[start:match.start()] + "[" + fecha_str + "]" + texto[match.end():end]
            
            # Agregar a las fechas encontradas si no existe ya
            if not any(f['valor'] == fecha_str for f in fechas_encontradas):
                fechas_encontradas.append({
                    'valor': fecha_str,
                    'contexto': contexto.strip()
                })
    
    if fechas_encontradas:
        texto_chunk = texto[:200] + '...' if len(texto) > 200 else texto
        resultados.append({
            'chunk_id': i,
            'texto': texto_chunk,
            'fechas': fechas_encontradas
        })

print(f"\nSe encontraron {len(resultados)} chunks con fechas.")

# Mostrar los resultados
for i, resultado in enumerate(resultados[:10]):  # Mostrar solo los primeros 10
    print(f"\n--- Resultado {i+1} ---")
    print(f"Texto: {resultado['texto']}")
    print("Fechas encontradas:")
    for fecha in resultado['fechas']:
        print(f"- {fecha['valor']} (Contexto: {fecha['contexto']})")
