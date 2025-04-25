import re

# Ruta del archivo de entrada y salida
ruta_entrada = "data/raw/resultado.txt"
ruta_salida = "data/processed/texto_limpio.txt"

def limpiar_texto(texto):
    # Eliminar caracteres raros o basura
    texto = re.sub(r'[^\x20-\x7E\náéíóúÁÉÍÓÚñÑ°•]', ' ', texto)

    # Reemplazar múltiples espacios por uno solo
    texto = re.sub(r'\s+', ' ', texto)

    # Asegurar saltos de línea donde corresponda (ejemplo básico)
    texto = re.sub(r'(\d+\.\d+)', r'\n\1', texto)  # Forzar salto en numerales tipo 8.4.17

    return texto.strip()

if __name__ == "__main__":
    with open(ruta_entrada, "r", encoding="utf-8") as f:
        texto_original = f.read()

    texto_limpio = limpiar_texto(texto_original)

    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(texto_limpio)

    print(f"✅ Texto limpio guardado en: {ruta_salida}")
