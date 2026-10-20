#!/usr/bin/env bash
set -euo pipefail
APP_DIR="/opt/bring-pi"
SERVICE_USER="${SUDO_USER:-$USER}"
PORT="8766"

if [[ $EUID -ne 0 ]]; then
  echo "Executa: sudo bash install.sh"
  exit 1
fi
if [[ ! -f app.py ]]; then
  echo "Erro: app.py não está na pasta atual."
  exit 1
fi
if ss -ltn | awk '{print $4}' | grep -Eq "(:|\\])${PORT}$"; then
  echo "ERRO: a porta $PORT já está ocupada. Não instalei."
  exit 1
fi

apt-get update
apt-get install -y python3-venv python3-pip
install -d -m 750 -o root -g "$SERVICE_USER" "$APP_DIR"
install -m 640 -o root -g "$SERVICE_USER" app.py "$APP_DIR/app.py"
install -m 640 -o root -g "$SERVICE_USER" requirements.txt "$APP_DIR/requirements.txt"
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

if [[ ! -f "$APP_DIR/config.env" ]]; then
  TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
  cat > "$APP_DIR/config.env" <<EOF
BRING_EMAIL=
BRING_PASSWORD=
BRING_WEB_TOKEN=$TOKEN
BRING_HOST=0.0.0.0
BRING_PORT=$PORT
EOF
  chmod 600 "$APP_DIR/config.env"
fi
chown root:"$SERVICE_USER" "$APP_DIR/config.env"
chmod 640 "$APP_DIR/config.env"

cat > /etc/systemd/system/bring-pi.service <<EOF
[Unit]
Description=Bring! Shopping List Web Service
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/config.env
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/app.py
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true
UMask=0077
[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable bring-pi.service
systemctl restart bring-pi.service
echo "Serviço configurado na porta $PORT."
echo "Edita: sudo nano $APP_DIR/config.env e preenche BRING_EMAIL e BRING_PASSWORD."
echo "Depois: sudo systemctl restart bring-pi"
echo "IP da Pi: hostname -I"
echo "Android: http://IP_DA_RASPBERRY:$PORT"
echo "Token de acesso: BRING_WEB_TOKEN em $APP_DIR/config.env"
echo "Não encaminhes a porta 8766 para a Internet."
