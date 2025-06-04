import pickle
import re
import os

# Ruta del vectorstore limpio
ruta_vectorstore = "data/processed/vectorstore_semantic_full_limpio.pkl"

def buscar_fecha_directiva():
    """
    Busca la fecha de publicación o aprobación de la directiva DI-003-02-MINEDU
    """
    # Verificar si existe el archivo
    if not os.path.exists(ruta_vectorstore):
        print(f"No se encontró el archivo: {ruta_vectorstore}")
        return
    
    # Cargar el vectorstore limpio
    with open(ruta_vectorstore, 'rb') as f:
        vectorstore = pickle.load(f)
    
    chunks = vectorstore['chunks']
    
    # Patrones para buscar fechas
    patrones_fecha = [
        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # dd/mm/yyyy
        r'\b\d{1,2}-\d{1,2}-\d{2,4}\b',  # dd-mm-yyyy
        r'\b\d{1,2} de [a-zA-ZáéíóúÁÉÍÓÚ]+ de \d{2,4}\b',  # dd de mes de yyyy
        r'\b\d{1,2} [a-zA-ZáéíóúÁÉÍÓÚ]+ \d{2,4}\b',  # dd mes yyyy
    ]
    
    # Palabras clave para buscar
    palabras_clave = [
        'directiva', 'DI-003', 'DI-003-02-MINEDU', 'MINEDU', 
        'fecha', 'publicación', 'publicada', 'emitida', 'aprobada', 'aprobación',
        'vigencia', 'vigente', 'resolución'
    ]
    
    # Buscar chunks relevantes
    chunks_relevantes = []
    for i, chunk in enumerate(chunks):
        texto = ""
        if isinstance(chunk, dict):
            texto = chunk.get('texto', '')
        else:
            texto = chunk
        
        texto_lower = texto.lower()
        
        # Verificar si el chunk contiene palabras clave
        if any(palabra.lower() in texto_lower for palabra in palabras_clave):
            # Buscar fechas en el texto
            fechas = []
            for patron in patrones_fecha:
                matches = re.finditer(patron, texto)
                for match in matches:
                    fecha = match.group(0)
                    # Obtener contexto
                    start = max(0, match.start() - 50)
                    end = min(len(texto), match.end() + 50)
                    contexto = texto[start:match.start()] + "[" + fecha + "]" + texto[match.end():end]
                    fechas.append({
                        'fecha': fecha,
                        'contexto': contexto.strip()
                    })
            
            if fechas:
                chunks_relevantes.append({
                    'chunk_id': i,
                    'texto': texto[:200] + '...' if len(texto) > 200 else texto,
                    'fechas': fechas
                })
    
    # Mostrar resultados
    print(f"\nSe encontraron {len(chunks_relevantes)} chunks relevantes con fechas.")
    
    for i, chunk in enumerate(chunks_relevantes):
        print(f"\n--- Chunk {i+1} (ID: {chunk['chunk_id']}) ---")
        print(f"Texto: {chunk['texto']}")
        print("Fechas encontradas:")
        for fecha in chunk['fechas']:
            print(f"- {fecha['fecha']}")
            print(f"  Contexto: {fecha['contexto']}")
        print("-" * 50)
    
    # Buscar específicamente la directiva DI-003-02-MINEDU
    print("\nBuscando específicamente la directiva DI-003-02-MINEDU:")
    for i, chunk in enumerate(chunks):
        texto = ""
        if isinstance(chunk, dict):
            texto = chunk.get('texto', '')
        else:
            texto = chunk
        
        if "DI-003-02-MINEDU" in texto or "DI-003" in texto:
            print(f"\nChunk {i}:")
            print(texto[:500] + '...' if len(texto) > 500 else texto)

if __name__ == "__main__":
    buscar_fecha_directiva()
