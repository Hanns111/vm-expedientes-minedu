#!/usr/bin/env python3
import os
import anthropic

def main():
    print("🤖 CLAUDE CODE TERMINAL")
    print("=" * 30)
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY no configurada")
        print("🔑 Para usar Claude, configura tu API key:")
        print("   $env:ANTHROPIC_API_KEY='tu_api_key_aqui'")
        return
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        print("✅ Cliente de Claude configurado")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print("💡 Escribe tu pregunta (o 'quit' para salir):")
    
    while True:
        try:
            user_input = input("\n🧑 Tú: ").strip()
            
            if user_input.lower() in ["quit", "exit"]:
                print("👋 ¡Hasta luego!")
                break
            
            if not user_input:
                continue
            
            print("🤖 Claude: Procesando...")
            
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                messages=[{"role": "user", "content": user_input}]
            )
            
            if response.content:
                reply = response.content[0].text
                print(f"🤖 Claude: {reply}")
            else:
                print("❌ No se recibió respuesta")
                
        except KeyboardInterrupt:
            print("\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
