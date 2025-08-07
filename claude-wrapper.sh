#!/bin/bash

# Wrapper para Claude Code CLI
# Carga automáticamente NVM y ejecuta Claude

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Ejecutar Claude con todos los argumentos pasados
~/.nvm/versions/node/v20.19.3/bin/claude "$@" 