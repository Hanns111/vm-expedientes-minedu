import re
import json

# Rutas de entrada y salida
ruta_entrada = "data/processed/texto_limpio.txt"
ruta_salida = "data/processed/chunks_v2.json"

def chunkear_texto(texto):
    # Expresión regular para detectar títulos de secciones (ej. 1. Objeto, 2. Finalidad, etc.)
    patron = re.compile(r'(\d+\.\s+[A-ZÁÉÍÓÚÑa-záéíóúñ\s]+)')

    secciones = patron.split(texto)
    chunks = []

    for i in range(1, len(secciones), 2):
        titulo = secciones[i].strip()
        contenido = secciones[i+1].strip() if i+1 < len(secciones) else ""
        chunks.append({
            "titulo": titulo,
            "texto": contenido
        })

    return chunks

if __name__ == "__main__":
    with open(ruta_entrada, "r", encoding="utf-8") as f:
        texto = f.read()

    chunks = chunkear_texto(texto)

    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"Chunking completado. Guardado en: {ruta_salida}")
