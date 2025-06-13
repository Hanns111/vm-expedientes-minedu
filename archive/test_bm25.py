import os
import sys

# Añadir directorio raíz al PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
    print(f"Añadido {current_dir} al PYTHONPATH")

from src.ai.search_vectorstore_bm25 import BM25Search

def main():
    # Usar la ruta al vectorstore BM25 que se menciona en los logs anteriores
    vectorstore_path = 'data/processed/vectorstore_bm25_test.pkl'
    search = BM25Search(vectorstore_path=vectorstore_path)
    results = search.search('¿Cuál es el monto máximo para viáticos?', top_k=3)
    print('Resultados encontrados:', len(results))
    
    # Inspeccionar la estructura de los resultados
    print('\nEstructura del primer resultado:')
    if results and len(results) > 0:
        first_result = results[0]
        print(f'Tipo de resultado: {type(first_result)}')
        if isinstance(first_result, dict):
            print('Claves disponibles:')
            for key in first_result.keys():
                print(f'  - {key}')
            
            # Intentar acceder a diferentes claves comunes
            for key in ['text', 'content', 'page_content', 'chunk', 'answer']:
                if key in first_result:
                    print(f'\nContenido de la clave "{key}":')
                    content = first_result[key]
                    print(f'{content[:200]}...' if len(content) > 200 else content)
                    
                    # Verificar si contiene "320"
                    if "320" in content:
                        print(f"\n✅ Encontrado monto '320' en la clave '{key}'")
    else:
        print('No se encontraron resultados')
        
    print('\nResultado completo (primeros 3):')
    import json
    print(json.dumps(results[:3], indent=2, ensure_ascii=False)[:1000] + '...' if len(json.dumps(results[:3])) > 1000 else json.dumps(results[:3], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
