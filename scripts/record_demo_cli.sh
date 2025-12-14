#!/bin/bash
# Xcapit Privacy - CLI Demo Recorder
#
# Usa asciinema para grabar la demo de terminal
# El resultado es un archivo .cast que se puede:
# - Subir a asciinema.org
# - Convertir a GIF con agg
# - Convertir a video con asciinema-player
#
# Requisitos:
#   brew install asciinema
#   pip install asciinema-agg  # Para convertir a GIF

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="$PROJECT_DIR/recordings"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CAST_FILE="$OUTPUT_DIR/demo_cli_$TIMESTAMP.cast"
GIF_FILE="$OUTPUT_DIR/demo_cli_$TIMESTAMP.gif"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  Xcapit Privacy - CLI Demo Recorder${NC}"
echo -e "${BLUE}======================================${NC}"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Check for asciinema
if ! command -v asciinema &> /dev/null; then
    echo -e "${YELLOW}asciinema no encontrado. Instalando...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install asciinema
    else
        pip install asciinema
    fi
fi

echo -e "\n${GREEN}Instrucciones:${NC}"
echo "1. La grabacion comenzara automaticamente"
echo "2. El script de demo se ejecutara"
echo "3. Presiona Enter en cada paso para avanzar"
echo "4. Al finalizar, la grabacion se guardara"
echo ""
echo -e "Archivo de salida: ${BLUE}$CAST_FILE${NC}"
echo ""
read -p "Presiona Enter para comenzar la grabacion..."

# Record the demo
echo -e "\n${GREEN}Iniciando grabacion...${NC}\n"

asciinema rec \
    --title "Xcapit Privacy - FHE Demo" \
    --idle-time-limit 2 \
    --command "cd $PROJECT_DIR && source .venv/bin/activate && python scripts/demo_fhe_transparency.py" \
    "$CAST_FILE"

echo -e "\n${GREEN}Grabacion guardada en:${NC} $CAST_FILE"

# Ask if user wants to convert to GIF
echo ""
read -p "¿Convertir a GIF? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    if ! command -v agg &> /dev/null; then
        echo -e "${YELLOW}Instalando agg (asciinema gif generator)...${NC}"
        pip install asciinema-agg 2>/dev/null || cargo install agg 2>/dev/null || {
            echo -e "${YELLOW}No se pudo instalar agg. Puedes hacerlo manualmente:${NC}"
            echo "  cargo install agg"
            echo "  o"
            echo "  pip install asciinema-agg"
        }
    fi

    if command -v agg &> /dev/null; then
        echo -e "${GREEN}Generando GIF...${NC}"
        agg "$CAST_FILE" "$GIF_FILE"
        echo -e "${GREEN}GIF guardado en:${NC} $GIF_FILE"
    fi
fi

# Ask if user wants to upload to asciinema.org
echo ""
read -p "¿Subir a asciinema.org? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}Subiendo...${NC}"
    asciinema upload "$CAST_FILE"
fi

echo -e "\n${GREEN}¡Listo!${NC}"
echo ""
echo "Archivos generados:"
echo "  - Cast: $CAST_FILE"
[ -f "$GIF_FILE" ] && echo "  - GIF:  $GIF_FILE"
echo ""
echo "Para reproducir la grabacion:"
echo "  asciinema play $CAST_FILE"
