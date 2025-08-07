import pickle
import re

# Cargar el vectorstore
with open('data/processed/vectorstore_semantic_full_v2.pkl', 'rb') as f:
    vectorstore = pickle.load(f)

chunks = vectorstore['chunks']

# Patrones simples para detectar números y posibles fechas
patron_numeros = r'\d+'
patron_fechas = r'\d{1,4}[/-]?\d{1,2}[/-]?\d{1,4}'

# Contador de chunks con números y posibles fechas
chunks_con_numeros = 0
chunks_con_fechas = 0

# Ejemplos de números y posibles fechas encontradas
ejemplos_numeros = []
ejemplos_fechas = []

# Revisar cada chunk
for i, chunk in enumerate(chunks):
    texto = chunk['texto']
    
    # Buscar números
    numeros = re.findall(patron_numeros, texto)
    if numeros:
        chunks_con_numeros += 1
        if len(ejemplos_numeros) < 5:
            ejemplos_numeros.append((i, numeros[:3], texto[:100]))
    
    # Buscar posibles fechas
    fechas = re.findall(patron_fechas, texto)
    if fechas:
        chunks_con_fechas += 1
        if len(ejemplos_fechas) < 5:
            ejemplos_fechas.append((i, fechas, texto[:100]))

# Mostrar resultados
print(f"\nTotal de chunks: {len(chunks)}")
print(f"Chunks con números: {chunks_con_numeros} ({(chunks_con_numeros/len(chunks))*100:.2f}%)")
print(f"Chunks con posibles fechas: {chunks_con_fechas} ({(chunks_con_fechas/len(chunks))*100:.2f}%)")

print("\nEjemplos de números encontrados:")
for i, nums, texto in ejemplos_numeros:
    print(f"Chunk {i}: {nums} - '{texto}...'")

print("\nEjemplos de posibles fechas encontradas:")
for i, fechas, texto in ejemplos_fechas:
    print(f"Chunk {i}: {fechas} - '{texto}...'")

# Verificar si hay texto que menciona "directiva" y "fecha"
print("\nBuscando menciones de 'directiva' y 'fecha':")
for i, chunk in enumerate(chunks):
    texto = chunk['texto'].lower()
    if 'directiva' in texto and ('fecha' in texto or 'publicación' in texto or 'emisión' in texto):
        print(f"\nChunk {i}:")
        print(texto[:200] + '...' if len(texto) > 200 else texto)
