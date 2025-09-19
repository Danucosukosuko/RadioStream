#!/bin/bash
set -euo pipefail

# ==============================
# Instalador RadioStream
# ==============================

# --- Configuración ---
REPO_URL="https://github.com/Danucosukosuko/RadioStream.git"
APP_NAME="radiostream"
INSTALL_DIR="/opt/$APP_NAME"
PYTHON_BIN="/usr/bin/python3"
SERVICE_FILE="/etc/systemd/system/$APP_NAME.service"

# --- Comprobar root ---
if [[ $EUID -ne 0 ]]; then
   echo "[ERROR] Este script debe ejecutarse como root (usa sudo)." >&2
   exit 1
fi

echo "📥 Clonando repositorio desde $REPO_URL..."
rm -rf "$INSTALL_DIR"
git clone "$REPO_URL" "$INSTALL_DIR"

echo "📦 Instalando dependencias..."
$PYTHON_BIN -m pip install --upgrade pip
$PYTHON_BIN -m pip install -r "$INSTALL_DIR/requirements.txt"

echo "⚙️ Creando servicio systemd..."
cat > "$SERVICE_FILE" <<EOL
[Unit]
Description=RadioStream Service
After=network.target

[Service]
WorkingDirectory=$INSTALL_DIR
ExecStart=$PYTHON_BIN $INSTALL_DIR/main.py
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOL

echo "🔄 Habilitando servicio..."
systemctl daemon-reload
systemctl enable "$APP_NAME"
systemctl start "$APP_NAME"

echo "✅ Instalación completada. El servicio '$APP_NAME' está en marcha."
echo "👉 Ver logs: journalctl -u $APP_NAME -f"
