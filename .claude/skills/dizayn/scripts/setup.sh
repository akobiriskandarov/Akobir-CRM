#!/usr/bin/env bash
# Yangi sessiyada bir marta: shriftlar, Python paketlari, AI modellar (fon olib tashlash, sifat oshirish).
set -e
DIR="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p ~/.fonts && cp "$DIR"/fonts/*.ttf ~/.fonts/ && fc-cache -f >/dev/null
python3 -c "import rembg" 2>/dev/null || pip install -q "rembg[cpu]"
python3 -c "import psd_tools, fontTools" 2>/dev/null || pip install -q psd-tools fonttools
python3 -c "import cv2; cv2.dnn_superres" 2>/dev/null || { pip uninstall -y -q opencv-python-headless opencv-python 2>/dev/null || true; pip install -q opencv-contrib-python-headless; }
SR=~/.cache/dizayn/sr; mkdir -p "$SR"
[ -f "$SR/ESPCN_x4.pb" ] || curl -sfL -o "$SR/ESPCN_x4.pb" https://raw.githubusercontent.com/fannymonori/TF-ESPCN/master/export/ESPCN_x4.pb
[ -f "$SR/EDSR_x4.pb" ] || curl -sfL -o "$SR/EDSR_x4.pb" https://raw.githubusercontent.com/Saafke/EDSR_Tensorflow/master/models/EDSR_x4.pb
python3 -c "from rembg import new_session; new_session('isnet-general-use')" >/dev/null 2>&1 || echo "! rembg modeli yuklanmadi (github.com kerak)"
node -e "require('playwright')" && echo "✓ dizayn tayyor"
