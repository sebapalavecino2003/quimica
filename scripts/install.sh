#!/usr/bin/env bash
# ==============================================================================
# Script de Instalación Automatizada e Idempotente
# Asistente Inteligente para Moodle con Gemini y Playwright
# ==============================================================================

set -e

# Colores para la salida
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}  Instalación del Asistente Moodle + Gemini         ${NC}"
echo -e "${BLUE}====================================================${NC}"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# 1. Verificar Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] python3 no está instalado en este sistema.${NC}"
    echo "Por favor instálelo con: sudo apt update && sudo apt install python3 python3-venv python3-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}[OK]${NC} Python detectado: versión ${PYTHON_VERSION}"

# 2. Crear entorno virtual si no existe
if [ ! -d ".venv" ]; then
    echo -e "${BLUE}[INFO]${NC} Creando entorno virtual en .venv..."
    python3 -m venv .venv
else
    echo -e "${GREEN}[OK]${NC} Entorno virtual .venv ya existente."
fi

# 3. Activar entorno virtual
source .venv/bin/activate

# 4. Actualizar pip
echo -e "${BLUE}[INFO]${NC} Actualizando pip..."
pip install --upgrade pip --quiet

# 5. Instalar dependencias
echo -e "${BLUE}[INFO]${NC} Instalando dependencias desde requirements.txt..."
pip install -r requirements.txt --quiet

# 6. Verificar instalación de Google Chrome oficial
echo -e "${BLUE}[INFO]${NC} Verificando Google Chrome oficial..."
if command -v google-chrome &> /dev/null || command -v google-chrome-stable &> /dev/null; then
    echo -e "${GREEN}[OK]${NC} Google Chrome oficial detectado."
else
    echo -e "${YELLOW}[AVISO]${NC} No se detectó Google Chrome oficial en el sistema."
    echo "El asistente utiliza Google Chrome (channel='chrome')."
    echo "Si no lo tiene instalado, descárguelo desde: https://www.google.com/chrome/"
fi

# 7. Configuración de archivo .env
if [ ! -f ".env" ]; then
    echo -e "${BLUE}[INFO]${NC} Creando archivo .env a partir de .env.example..."
    cp .env.example .env
    echo -e "${YELLOW}[ATENCIÓN]${NC} Se creó el archivo .env. Debes editarlo y configurar tu GEMINI_API_KEY."
else
    echo -e "${GREEN}[OK]${NC} Archivo .env ya presente."
fi

# 8. Permisos de ejecución
chmod +x scripts/install.sh scripts/run.sh 2>/dev/null || true

echo -e "${GREEN}====================================================${NC}"
echo -e "${GREEN}  ¡Instalación completada con éxito!                ${NC}"
echo -e "${GREEN}====================================================${NC}"
echo -e "Pasos siguientes:"
echo -e " 1. Edita el archivo ${BLUE}.env${NC} y coloca tu clave de API:"
echo -e "    ${YELLOW}GEMINI_API_KEY=tu_clave_aqui${NC}"
echo -e " 2. Ejecuta el asistente con:"
echo -e "    ${GREEN}./scripts/run.sh${NC}"

