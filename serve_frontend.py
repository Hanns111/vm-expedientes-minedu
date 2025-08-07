#!/usr/bin/env python3
"""
Servidor simple para frontend HTML
"""
import http.server
import socketserver
import os
from pathlib import Path

# Cambiar al directorio del proyecto
project_root = Path(__file__).parent
os.chdir(project_root)

PORT = 3000

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Permitir CORS para desarrollo
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self):
        # Servir frontend_simple.html como índice
        if self.path == '/' or self.path == '/index.html':
            self.path = '/frontend_simple.html'
        return super().do_GET()

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        print(f"🌐 Frontend servido en http://localhost:{PORT}")
        print(f"📁 Directorio: {project_root}")
        print("✨ Abre tu navegador en http://localhost:3000")
        print("🔄 Ctrl+C para detener")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Servidor detenido")