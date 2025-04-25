import re
import json

def leer_texto(ruta_txt):
    with open(ruta_txt, "r", encoding="utf-8") as archivo:
        texto = archivo.read()
        texto_limpio = texto.replace('\n', ' ').replace('\r', '').strip()
        return re.sub(r'\s{2,}', ' ', texto_limpio)  # Elimina espacios dobles+

def extraer_info(texto):
    datos = {
        "numero_directiva": None,
        "entidad_emisora": None,
        "fecha_emision": None,
        "unidad_responsable": None,
        "objetivo": None
    }

    # Número de directiva
    match_directiva = re.search(r"(Directiva\s+N[°º]?\s*\d{3}-\d{4}-[A-Z]+)", texto)
    if match_directiva:
        datos["numero_directiva"] = match_directiva.group(1)

    # Entidad emisora
    match_entidad = re.search(r"(MINEDU|Ministerio\s+de\s+Educación)", texto, re.IGNORECASE)
    if match_entidad:
        datos["entidad_emisora"] = match_entidad.group(1).upper()

    # Fecha (busca algo como "Lima, 10 de noviembre de 2020")
    match_fecha = re.search(r"(Lima,?\s+\d{1,2}\s+de\s+\w+\s+de\s+\d{4})", texto, re.IGNORECASE)
    if match_fecha:
        datos["fecha_emision"] = match_fecha.group(1)

    # Unidad responsable
    match_unidad = re.search(r"Unidad\s+Responsable\s*:?[\s\-]*([A-Z].+?)(\.|,)", texto)
    if match_unidad:
        datos["unidad_responsable"] = match_unidad.group(1).strip()

    # Objetivo
    match_objetivo = re.search(r"(?i)objetivo\s*:?(.{30,300})", texto)
    if match_objetivo:
        datos["objetivo"] = match_objetivo.group(1).strip()

    return datos

def guardar_json(datos, ruta_salida):
    with open(ruta_salida, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, indent=4, ensure_ascii=False)

def main():
    ruta_txt = "data/raw/resultado_limpio.txt"
    ruta_json = "data/processed/directiva_011_2020.json"

    texto = leer_texto(ruta_txt)
    info = extraer_info(texto)
    guardar_json(info, ruta_json)
    print("✅ Información actualizada y guardada en JSON.")

if __name__ == "__main__":
    main()
