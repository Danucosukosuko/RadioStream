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

# --- Comprobar git ---
if ! command -v git >/dev/null 2>&1; then
    echo "⚠️  Git no está instalado. Instalando con apt..."
    apt update -y
    apt install -y git
fi

# --- Copia de seguridad de config.json y static ---
if [[ -d "$INSTALL_DIR" ]]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_DIR="${INSTALL_DIR}_backup_$TIMESTAMP"
    mkdir -p "$BACKUP_DIR"
    echo "💾 Haciendo backup de config.json y static en $BACKUP_DIR..."
    [[ -f "$INSTALL_DIR/config.json" ]] && cp "$INSTALL_DIR/config.json" "$BACKUP_DIR/"
    [[ -d "$INSTALL_DIR/static" ]] && cp -r "$INSTALL_DIR/static" "$BACKUP_DIR/"
    echo "🗑 Borrando directorio viejo $INSTALL_DIR..."
    rm -rf "$INSTALL_DIR"
fi

# --- Clonar repo ---
echo "📥 Clonando repositorio desde $REPO_URL..."
git clone "$REPO_URL" "$INSTALL_DIR"

# --- Restaurar backup si existe ---
if [[ -d "$BACKUP_DIR" ]]; then
    echo "🔄 Restaurando config.json y static..."
    [[ -f "$BACKUP_DIR/config.json" ]] && cp "$BACKUP_DIR/config.json" "$INSTALL_DIR/"
    [[ -d "$BACKUP_DIR/static" ]] && cp -r "$BACKUP_DIR/static" "$INSTALL_DIR/"
fi

# --- Instalar requirements ---
REQ_FILE="$INSTALL_DIR/requirements.txt"
if [[ -f "$REQ_FILE" ]]; then
    echo "📦 Instalando dependencias desde requirements.txt..."
    $PYTHON_BIN -m pip install --upgrade pip
    $PYTHON_BIN -m pip install -r "$REQ_FILE"
else
    echo "⚠️ No se encontró requirements.txt en el repo."
fi

# --- Crear servicio systemd ---
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

# --- Activar servicio ---
systemctl daemon-reload
systemctl enable "$APP_NAME"
systemctl restart "$APP_NAME"

echo "✅ Instalación completada. Servicio '$APP_NAME' activo."
echo "👉 Ver logs: journalctl -u $APP_NAME -f"
