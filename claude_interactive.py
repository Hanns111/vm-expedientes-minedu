#!/usr/bin/env python3
"""
Claude Interactive Terminal
Permite interactuar con Claude AI desde la terminal
"""

import os
import sys
import anthropic
from typing import Optional
import json
import datetime

class ClaudeInteractive:
    def __init__(self):
        self.client = None
        self.conversation_history = []
        self.setup_client()
    
    def setup_client(self):
        """Configura el cliente de Claude"""
        # Buscar API key en variables de entorno
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            print("⚠️  ANTHROPIC_API_KEY no encontrada en variables de entorno")
            print("🔑 Para usar Claude, necesitas configurar tu API key:")
            print("   set ANTHROPIC_API_KEY=tu_api_key_aqui")
            print("   o")
            print("   export ANTHROPIC_API_KEY=tu_api_key_aqui")
            return
        
        try:
            self.client = anthropic.Anthropic(api_key=api_key)
            print("✅ Cliente de Claude configurado correctamente")
        except Exception as e:
            print(f"❌ Error configurando Claude: {e}")
    
    def send_message(self, message: str) -> Optional[str]:
        """Envía un mensaje a Claude"""
        if not self.client:
            return "❌ Cliente de Claude no configurado"
        
        try:
            # Preparar el historial de conversación
            messages = []
            for item in self.conversation_history[-10:]:  # Solo últimos 10 mensajes
                messages.append({
                    "role": item["role"],
                    "content": item["content"]
                })
            
            # Agregar mensaje actual
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Enviar a Claude
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                messages=messages
            )
            
            # Procesar respuesta
            if response.content:
                reply = response.content[0].text
                
                # Guardar en historial
                self.conversation_history.append({
                    "role": "user",
                    "content": message,
                    "timestamp": datetime.datetime.now().isoformat()
                })
                self.conversation_history.append({
                    "role": "assistant", 
                    "content": reply,
                    "timestamp": datetime.datetime.now().isoformat()
                })
                
                return reply
            else:
                return "❌ No se recibió respuesta de Claude"
                
        except Exception as e:
            return f"❌ Error enviando mensaje: {e}"
    
    def show_help(self):
        """Muestra la ayuda del sistema"""
        help_text = """
🤖 CLAUDE INTERACTIVE TERMINAL
==============================

Comandos disponibles:
  /help      - Mostrar esta ayuda
  /history   - Ver historial de conversación
  /clear     - Limpiar historial
  /save      - Guardar historial en archivo
  /load      - Cargar historial desde archivo
  /exit      - Salir del programa
  /quit      - Salir del programa

Uso:
  - Escribe tu pregunta o mensaje directamente
  - Claude responderá usando el modelo claude-3-haiku
  - El historial se mantiene durante la sesión

Ejemplos:
  > ¿Cómo funciona el sistema RAG del proyecto?
  > Analiza el código en src/ai/hybrid_search.py
  > Explica la arquitectura de microservicios

Configuración:
  - Requiere ANTHROPIC_API_KEY en variables de entorno
  - Modelo: claude-3-haiku-20240307
  - Historial: últimos 10 mensajes
"""
        print(help_text)
    
    def show_history(self):
        """Muestra el historial de conversación"""
        if not self.conversation_history:
            print("📝 No hay historial de conversación")
            return
        
        print("\n📜 HISTORIAL DE CONVERSACIÓN")
        print("=" * 50)
        
        for i, item in enumerate(self.conversation_history[-20:], 1):
            role = "🧑 Usuario" if item["role"] == "user" else "🤖 Claude"
            timestamp = item.get("timestamp", "")
            content = item["content"][:100] + "..." if len(item["content"]) > 100 else item["content"]
            
            print(f"{i}. {role} [{timestamp}]:")
            print(f"   {content}")
            print()
    
    def clear_history(self):
        """Limpia el historial de conversación"""
        self.conversation_history = []
        print("🗑️  Historial limpiado")
    
    def save_history(self, filename: str = None):
        """Guarda el historial en un archivo"""
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"claude_history_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, indent=2, ensure_ascii=False)
            print(f"💾 Historial guardado en: {filename}")
        except Exception as e:
            print(f"❌ Error guardando historial: {e}")
    
    def load_history(self, filename: str):
        """Carga el historial desde un archivo"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.conversation_history = json.load(f)
            print(f"📂 Historial cargado desde: {filename}")
        except Exception as e:
            print(f"❌ Error cargando historial: {e}")
    
    def run(self):
        """Ejecuta el bucle principal del programa"""
        print("🤖 CLAUDE INTERACTIVE TERMINAL")
        print("=" * 40)
        print("💡 Escribe '/help' para ver comandos disponibles")
        print("🚪 Escribe '/exit' o '/quit' para salir")
        print()
        
        if not self.client:
            print("⚠️  Claude no está configurado. Configura ANTHROPIC_API_KEY primero.")
            return
        
        while True:
            try:
                user_input = input("\n🧑 Tú: ").strip()
                
                if not user_input:
                    continue
                
                # Comandos especiales
                if user_input.lower() in ['/exit', '/quit']:
                    print("👋 ¡Hasta luego!")
                    break
                elif user_input.lower() == '/help':
                    self.show_help()
                    continue
                elif user_input.lower() == '/history':
                    self.show_history()
                    continue
                elif user_input.lower() == '/clear':
                    self.clear_history()
                    continue
                elif user_input.lower().startswith('/save'):
                    parts = user_input.split(' ', 1)
                    filename = parts[1] if len(parts) > 1 else None
                    self.save_history(filename)
                    continue
                elif user_input.lower().startswith('/load'):
                    parts = user_input.split(' ', 1)
                    if len(parts) > 1:
                        self.load_history(parts[1])
                    else:
                        print("❌ Especifica el archivo: /load filename.json")
                    continue
                
                # Enviar mensaje a Claude
                print("🤖 Claude: Procesando...")
                response = self.send_message(user_input)
                print(f"🤖 Claude: {response}")
                
            except KeyboardInterrupt:
                print("\n\n👋 ¡Hasta luego!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    """Función principal"""
    claude = ClaudeInteractive()
    claude.run()

if __name__ == "__main__":
    main()
