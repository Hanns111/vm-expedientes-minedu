import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

ruta_pdf = "data/raw/Directiva_Viacos_011_2020.pdf"

# Abre el PDF con PyMuPDF
doc = fitz.open(ruta_pdf)

texto = ""

for pagina in doc:
    pix = pagina.get_pixmap(dpi=300)  # renderiza la página como imagen
    imagen_bytes = pix.tobytes("png")
    imagen = Image.open(io.BytesIO(imagen_bytes))
    
    texto += pytesseract.image_to_string(imagen, lang="spa")  # OCR en español
    texto += "\n\n"

doc.close()

print(texto[:1000])  # muestra los primeros 1000 caracteres
