#!/bin/bash
set -euo pipefail
REPO="https://github.com/andrefpgomes/twitchpiv2.git"; BASE="/opt/twitch-pi"; LOG="/var/log/twitchpi-install.log"
exec > >(tee -a "$LOG") 2>&1
[ "$(id -u)" -eq 0 ] || { echo 'Execute: sudo bash install-all.sh'; exit 1; }
echo '=== TwitchPi v2 - instalação completa ==='
apt-get update; apt-get install -y git python3 curl ca-certificates sudo
if command -v pihole >/dev/null 2>&1; then echo '[OK] Pi-hole já instalado; configuração preservada.'; else echo '[+] A instalar Pi-hole pelo instalador oficial...'; curl -fsSL https://install.pi-hole.net -o /tmp/pihole-install.sh; bash /tmp/pihole-install.sh; rm -f /tmp/pihole-install.sh; fi
if command -v chromium >/dev/null 2>&1 || command -v chromium-browser >/dev/null 2>&1; then echo '[OK] Chromium já instalado.'; else apt-get install -y chromium; fi
mkdir -p "$BASE/web" "$BASE/backups"; TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT; git clone --depth 1 "$REPO" "$TMP/repo"
cp -f "$TMP/repo/server.py" "$BASE/server.py"; cp -f "$TMP/repo/drops_tracker.py" "$BASE/drops_tracker.py"; cp -f "$TMP/repo/twitch_oauth.py" "$BASE/twitch_oauth.py"; cp -f "$TMP/repo/drops_config.json" "$BASE/drops_config.json"; cp -f "$TMP/repo/web/index.html" "$BASE/web/index.html"; cp -f "$TMP/repo/web/app.js" "$BASE/web/app.js"; cp -f "$TMP/repo/web/style.css" "$BASE/web/style.css"
[ -f "$BASE/state.json" ] || printf '{"channel":"","status":"stopped","favorites":[]}' > "$BASE/state.json"
[ -f "$BASE/config.env" ] || printf '# Local TwitchPi secrets. Do not commit this file.\n# TWITCH_CLIENT_ID=\n# TWITCH_OAUTH_TOKEN=\n# TWITCH_REFRESH_TOKEN=\n' > "$BASE/config.env"; chmod 600 "$BASE/config.env"
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
chmod 755 "$BASE/server.py" "$BASE/drops_tracker.py" "$BASE/twitch_oauth.py"; mkdir -p /home/andre/.config/twitch-pi-chromium; chown -R andre:andre /home/andre/.config/twitch-pi-chromium
systemctl daemon-reload; systemctl enable --now twitch-pi.service
IP=$(hostname -I | awk '{print $1}')
echo; echo '=== INSTALAÇÃO CONCLUÍDA ==='; echo "Pi-hole : http://$IP/admin"; echo "TwitchPi: http://$IP:8765"; echo "Serviço : $(systemctl is-active twitch-pi.service)"; echo "Drops   : Fortnite / Minecraft / Rocket League"; echo "OAuth   : configurar no painel TwitchPi"; echo "Log     : $LOG"
