import json

# Cargar chunks
with open('data/processed/chunks_directiva_limpia.json', 'r', encoding='utf-8') as f:
    chunks = json.load(f)

print(f"Total chunks: {len(chunks)}")
print("="*50)

# Buscar términos específicos
terminos = ['320', 'viático', 'viáticos', 'soles', 'S/', 'monto', 'responsabilidad']

for termino in terminos:
    print(f"\n🔍 Buscando: '{termino}'")
    encontrados = 0
    for i, chunk in enumerate(chunks):
        if termino.lower() in chunk['text'].lower():
            print(f"  ✅ Chunk {i} - Páginas: {chunk['pages']}")
            # Mostrar parte del texto donde aparece
            texto = chunk['text'].lower()
            inicio = max(0, texto.find(termino.lower()) - 50)
            fin = min(len(texto), texto.find(termino.lower()) + 100)
            contexto = chunk['text'][inicio:fin]
            print(f"     ...{contexto}...")
            encontrados += 1
    
    if encontrados == 0:
        print(f"  ❌ No encontrado")
    print("-"*30)