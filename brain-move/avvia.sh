#!/bin/bash

cd "$(dirname "$0")"

echo "=== Brain-Move - Avvio ==="
echo ""

# Controlla Python
if ! command -v python3 &>/dev/null; then
    echo "ERRORE: Python3 non trovato"
    exit 1
fi

# Installa dipendenze se mancanti
if ! python3 -c "import pygame, cv2, mediapipe" 2>/dev/null; then
    echo "Installazione dipendenze..."
    pip install -r requirements.txt
    echo ""
fi

# Avvia
echo "Avvio Brain-Move..."
echo "(Premi ESC per uscire)"
echo ""
python3 main.py "$@"
