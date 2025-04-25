def limpiar_texto(texto):
    import re
    texto = texto.replace("�", "")  # Elimina caracteres basura
    texto = re.sub(r'(\w)-\s+(\w)', r'\1\2', texto)  # Une palabras partidas
    texto = texto.replace('\n', ' ')  # Reemplaza saltos de línea por espacios
    texto = re.sub(r'\s{2,}', ' ', texto)  # Elimina espacios múltiples
    return texto.strip()

def guardar_texto_limpio(texto, ruta_salida):
    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(texto)

def main():
    ruta_entrada = "data/raw/resultado.txt"
    ruta_salida = "data/raw/resultado_limpio.txt"

    with open(ruta_entrada, "r", encoding="utf-8") as archivo:
        texto_crudo = archivo.read()

    texto_limpio = limpiar_texto(texto_crudo)
    guardar_texto_limpio(texto_limpio, ruta_salida)
    print(texto_limpio[:500])  # Muestra los primeros 500 caracteres del texto limpio
    print("✅ Texto limpiado y guardado en resultado_limpio.txt")

if __name__ == "__main__":
    main()
