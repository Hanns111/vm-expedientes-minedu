import os

def dividir_en_chunks(texto, max_palabras=300):
    palabras = texto.split()
    chunks = []
    for i in range(0, len(palabras), max_palabras):
        chunk = " ".join(palabras[i:i + max_palabras])
        chunks.append(chunk)
    return chunks

def main():
    ruta_entrada = "data/raw/resultado_limpio.txt"
    ruta_salida = "data/processed/chunks.txt"

    if not os.path.exists(ruta_entrada):
        print("❌ No se encuentra el archivo:", ruta_entrada)
        return

    with open(ruta_entrada, "r", encoding="utf-8") as archivo:
        texto = archivo.read()

    chunks = dividir_en_chunks(texto)

    with open(ruta_salida, "w", encoding="utf-8") as archivo:
        for i, chunk in enumerate(chunks):
            archivo.write(f"\n--- CHUNK {i+1} ---\n")
            archivo.write(chunk + "\n")

    print(f"✅ Se han generado {len(chunks)} chunks y guardado en {ruta_salida}")

if __name__ == "__main__":
    main()
