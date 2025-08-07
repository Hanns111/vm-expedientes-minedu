#!/bin/bash

# Cargar NVM primero
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Configurar alias persistente para Claude con ruta completa
echo "✅ Configurando alias 'claude' en ~/.bashrc..."
echo "alias claude='~/.nvm/versions/node/v20.19.3/bin/claude'" >> ~/.bashrc

# Configurar entorno NVM si aún no está
echo "✅ Configurando soporte NVM..."
echo 'export NVM_DIR="$HOME/.nvm"' >> ~/.bashrc
echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"' >> ~/.bashrc

# Aplicar cambios sin reiniciar
echo "✅ Aplicando configuración..."
source ~/.bashrc

echo "🎉 Claude Code está listo para usarse con el comando: claude"
echo "📍 Ubicación: ~/.nvm/versions/node/v20.19.3/bin/claude" 