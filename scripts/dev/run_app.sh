#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
export QT_MAC_WANTS_LAYER=1
python src/main.py
