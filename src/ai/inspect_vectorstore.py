import pickle

with open('data/processed/vectorstore_semantic_full_v2.pkl', 'rb') as f:
    vectorstore = pickle.load(f)

print("Claves disponibles en el vectorstore:")
print(vectorstore.keys())

# Mostrar los primeros 5 chunks
print("\nPrimeros 5 chunks:")
for i, chunk in enumerate(vectorstore['chunks'][:5]):
    print(f"\nChunk {i+1}:")
    print(chunk['texto'][:200] + '...')
