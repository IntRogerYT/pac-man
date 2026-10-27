#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

VENV=".venv"

echo "[*] Installing PyInstaller inside virtual environment..."
${VENV}/bin/pip install pyinstaller

echo "[*] Cleaning previous builds..."
rm -rf build/ dist/ pac-man.spec

echo "[*] Building standalone Pac-Man executable..."
# Use the pyinstaller executable directly from the virtual environment
${VENV}/bin/pyinstaller --name "pac-man" \
            --onedir \
            --windowed \
            --add-data "assets:assets" \
            --add-data "config.json:." \
            --add-data "libs:libs" \
            --hidden-import "mazegenerator" \
            pac-man.py

echo "[*] Ensuring config.json is available in the root of the package..."
cp config.json dist/pac-man/

echo "[*] Adding in-package instructions..."
cat << 'EOF' > dist/pac-man/instructions.txt
PAC-MAN - INSTRUCTIONS
----------------------
Controls:
- Arrow Keys or W, A, S, D to move
- P or ESC to Pause
- ESC to exit menus

How to Run:
Navigate into the extracted folder and launch the executable passing the config file as an argument:
    ./pac-man config.json
EOF

echo "[*] Zipping the final package..."
cd dist
python3 -m zipfile -c pac-man-release.zip pac-man/
cd ..

echo "[*] Build complete! Package ready at: dist/pac-man-release.zip"