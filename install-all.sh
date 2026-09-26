#!/bin/bash
set -euo pipefail
REPO="https://github.com/andrefpgomes/twitchpiv2.git"
BASE="/opt/twitch-pi"
LOG="/var/log/twitchpi-install.log"
exec > >(tee -a "$LOG") 2>&1

if [ "$(id -u)" -ne 0 ]; then echo "Execute: sudo bash install-all.sh"; exit 1; fi

echo "=== TwitchPi v2 - instalação completa ==="
apt-get update
apt-get install -y git python3 curl ca-certificates sudo

if command -v pihole >/dev/null 2>&1; then
  echo "[OK] Pi-hole já instalado; configuração preservada."
else
  echo "[+] Pi-hole não encontrado; a instalar pelo instalador oficial..."
  curl -fsSL https://install.pi-hole.net -o /tmp/pihole-install.sh
  bash /tmp/pihole-install.sh
  rm -f /tmp/pihole-install.sh
fi

if command -v chromium >/dev/null 2>&1 || command -v chromium-browser >/dev/null 2>&1; then
  echo "[OK] Chromium já instalado."
else
  echo "[+] A instalar Chromium..."
  apt-get install -y chromium
fi

mkdir -p "$BASE/web" "$BASE/backups"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
git clone --depth 1 "$REPO" "$TMP/repo"

cp -f "$TMP/repo/server.py" "$BASE/server.py"
cp -f "$TMP/repo/web/index.html" "$BASE/web/index.html"
cp -f "$TMP/repo/web/app.js" "$BASE/web/app.js"
cp -f "$TMP/repo/web/style.css" "$BASE/web/style.css"

if [ ! -f "$BASE/state.json" ]; then
  printf '{"channel":"","status":"stopped","favorites":[]}' > "$BASE/state.json"
fi

cat > /etc/systemd/system/twitch-pi.service <<EOF
[Unit]
Description=TwitchPi Web Controller
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=$BASE
Environment=PORT=8765
Environment=STATE_FILE=$BASE/state.json
Environment=TWITCH_USER=andre
Environment=TWITCH_UID=1000
Environment=TWITCH_PROFILE=/home/andre/.config/twitch-pi-chromium
ExecStart=/usr/bin/python3 $BASE/server.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

chmod 755 "$BASE/server.py"
mkdir -p /home/andre/.config/twitch-pi-chromium
chown -R andre:andre /home/andre/.config/twitch-pi-chromium
systemctl daemon-reload
systemctl enable --now twitch-pi.service
IP=$(hostname -I | awk '{print $1}')
echo
echo "=== INSTALAÇÃO CONCLUÍDA ==="
echo "Pi-hole : http://$IP/admin"
echo "TwitchPi: http://$IP:8765"
echo "Serviço : $(systemctl is-active twitch-pi.service)"
echo "Login   : Chromium será aberto na sessão gráfica de andre"
echo "Log     : $LOG"
