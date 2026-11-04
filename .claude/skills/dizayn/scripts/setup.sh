#!/usr/bin/env bash
# Yangi sessiyada bir marta: shriftlarni tizimga o'rnatish + rembg (fon olib tashlash).
set -e
DIR="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p ~/.fonts && cp "$DIR"/fonts/*.ttf ~/.fonts/ && fc-cache -f >/dev/null
python3 -c "import rembg" 2>/dev/null || pip install -q "rembg[cpu]"
node -e "require('playwright')" && echo "✓ dizayn tayyor"
