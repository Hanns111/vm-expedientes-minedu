import subprocess

# Ruta del PDF de prueba y archivo de salida
ruta_pdf = "data/raw/Directiva_Viatcos_011_2020.pdf"
ruta_txt = "data/raw/resultado.txt"

# Ruta completa al ejecutable pdftotext
ejecutable = r"C:\plopper\bin\pdftotext.exe"

# Ejecutar pdftotext
subprocess.run([ejecutable, ruta_pdf, ruta_txt])

# Leer y mostrar los primeros caracteres del resultado
with open(ruta_txt, "r", encoding="utf-8") as archivo:
    texto = archivo.read()
    print(texto[:1000])  # Muestra los primeros 1000 caracteres
