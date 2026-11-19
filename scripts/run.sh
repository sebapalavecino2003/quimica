#!/usr/bin/env bash
# ==============================================================================
# Script de Ejecución del Asistente Moodle + Gemini
# ==============================================================================

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# 1. Comprobar que existe el entorno virtual
if [ ! -d ".venv" ]; then
    echo "[ERROR] No se encontró el entorno virtual .venv."
    echo "Ejecute primero el instalador: ./scripts/install.sh"
    exit 1
fi

# 2. Activar entorno virtual
source .venv/bin/activate

# 3. Comprobar dependencias básicas
if ! python -c "import playwright, google.genai, dotenv, pydantic" &> /dev/null; then
    echo "[AVISO] Faltan dependencias en el entorno. Reinstalando..."
    pip install -r requirements.txt --quiet
fi

# 4. Ejecutar el asistente principal
python main.py "$@"

