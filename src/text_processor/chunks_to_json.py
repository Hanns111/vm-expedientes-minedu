import json

def leer_chunks(ruta_txt):
    with open(ruta_txt, "r", encoding="utf-8") as archivo:
        contenido = archivo.read()
    bloques = contenido.split("--- CHUNK")
    chunks = []

    for bloque in bloques:
        bloque = bloque.strip()
        if bloque:
            partes = bloque.split("---")
            if len(partes) > 1:
                texto = partes[1].strip()
                chunks.append(texto)
    return chunks

def guardar_json(chunks, ruta_salida):
    data = [{"id": i+1, "texto": chunk} for i, chunk in enumerate(chunks)]
    with open(ruta_salida, "w", encoding="utf-8") as archivo:
        json.dump(data, archivo, indent=4, ensure_ascii=False)
    print(f"✅ Se guardó el JSON con {len(chunks)} chunks en {ruta_salida}")

def main():
    ruta_txt = "data/processed/chunks.txt"
    ruta_json = "data/processed/chunks.json"

    chunks = leer_chunks(ruta_txt)
    guardar_json(chunks, ruta_json)

if __name__ == "__main__":
    main()
