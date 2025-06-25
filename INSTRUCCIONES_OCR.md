# 🚀 INSTRUCCIONES PARA PROCESAR PDF REAL CON OCR PIPELINE

## 📦 1. INSTALAR DEPENDENCIAS

```bash
# Dependencias básicas
pip install paddleocr opencv-python pillow pdf2image

# Layout detection (opcional pero recomendado)
pip install 'layoutparser[layoutmodels,tesseract,paddledetection]'

# Si tienes problemas con layoutparser, instala solo estas:
pip install paddleocr opencv-python pillow pdf2image numpy
```

## 🧪 2. PROBAR INSTALACIÓN

```bash
# Test básico (sin dependencias externas)
python test_structure_only.py

# Test completo (con dependencias)  
python test_ocr_pipeline.py
```

## 📄 3. PROCESAR PDF REAL

```bash
# Procesar directiva_de_viaticos_011_2020_imagen.pdf
python process_real_directiva.py
```

**Este script:**
- ✅ Verifica dependencias instaladas
- ✅ Procesa el PDF escaneado con OCR
- ✅ Extrae entidades legales y financieras  
- ✅ Crea chunks inteligentes con metadatos
- ✅ Busca respuestas a las 3 consultas específicas
- ✅ Guarda resultados en `data/processed/chunks.json`

## 🎯 4. PROBAR CONSULTAS ESPECÍFICAS

```bash
# Test con el demo existente
python demo.py "¿Cuánto pueden gastar los ministros en viáticos?"
python demo.py "¿Qué numeral establece el límite de S/ 30?"
python demo.py "¿Cuánto corresponde de viáticos diarios en Lima?"
```

## 📊 5. RESULTADOS ESPERADOS

### Entidades que debería extraer:
- **Montos**: S/ 30.00, S/ 320.00, S/ 380.00, S/ 350.00
- **Porcentajes**: 30%
- **Numerales**: 8.4, 8.4.17, 8.5
- **Roles**: Ministros, Servidores Civiles, Funcionarios
- **Referencias**: Decreto Supremo N° 007-2013-EF
- **Procedimientos**: Declaración Jurada, rendición de cuentas

### Chunks con contexto:
- ✅ Jerarquía legal preservada (8 > 8.4 > 8.4.17)
- ✅ Metadatos enriquecidos (`role_level`, `has_amounts`)
- ✅ Compatible con sistema híbrido existente
- ✅ Ranking mejorado para ministros vs civiles

## 🔧 6. SOLUCIÓN DE PROBLEMAS

### Si tienes errores de dependencias:
```bash
# Instalar versiones específicas que funcionan
pip install paddleocr==2.7.3
pip install opencv-python==4.8.1.78  
pip install pillow==10.0.0
pip install pdf2image==1.16.3
```

### Si layoutparser da problemas:
- El pipeline funciona sin layoutparser (usa fallback a OpenCV)
- Solo instala las dependencias básicas arriba

### Si PaddleOCR es muy lento:
- En la primera ejecución descarga modelos (normal)
- Usa `use_gpu=False` en OCREngine para CPU

## ✅ 7. VERIFICACIÓN DE ÉXITO

El procesamiento fue exitoso si ves:
- ✅ "Processing completed successfully"
- ✅ Chunks creados > 5
- ✅ Entidades extraídas > 10
- ✅ "chunks.json" actualizado
- ✅ Respuestas a las 3 consultas específicas

## 🎉 8. DESPUÉS DEL PROCESAMIENTO

```bash
# Comparar antes/después
python src/ocr_pipeline/migrate_to_ocr.py

# Ver mejoras en ranking
python demo.py "¿Cuánto pueden gastar los ministros vs servidores civiles?"
```

## 📈 9. ESCALABILIDAD 

Una vez funcionando con 1 PDF:
- ✅ Procesar lotes: `processor.process_batch(['pdf1.pdf', 'pdf2.pdf'])`
- ✅ Paralelización: Ajustar `max_workers` en batch processing
- ✅ Millones de docs: Usar pipeline distribuido con Kubernetes

---

**¡El OCR pipeline está listo para procesar el documento real!** 🚀