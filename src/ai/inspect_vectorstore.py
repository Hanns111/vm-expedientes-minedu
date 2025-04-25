import pickle

with open('data/processed/vectorstore_semantic_v2.pkl', 'rb') as f:
    vectorstore = pickle.load(f)

print("🔍 Claves disponibles en el vectorstore:")
print(vectorstore.keys())
