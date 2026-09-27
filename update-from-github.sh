#!/bin/bash
set -euo pipefail
REPO="https://github.com/andrefpgomes/twitchpiv2.git"; BASE="/opt/twitch-pi"
[ "$(id -u)" -eq 0 ] || { echo 'Execute: sudo bash update-from-github.sh'; exit 1; }; [ -d "$BASE" ] || { echo "TwitchPi não está instalado em $BASE. Use install-all.sh."; exit 1; }
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT; git clone --depth 1 "$REPO" "$TMP/repo"
B="$BASE/backups/$(date +%Y%m%d-%H%M%S)"; mkdir -p "$B"; cp -a "$BASE/server.py" "$B/" 2>/dev/null || true; cp -a "$BASE/drops_tracker.py" "$B/" 2>/dev/null || true; cp -a "$BASE/drops_config.json" "$B/" 2>/dev/null || true; cp -a "$BASE/web" "$B/" 2>/dev/null || true
cp -f "$TMP/repo/server.py" "$BASE/server.py"; cp -f "$TMP/repo/drops_tracker.py" "$BASE/drops_tracker.py"; [ -f "$BASE/drops_config.json" ] || cp -f "$TMP/repo/drops_config.json" "$BASE/drops_config.json"; mkdir -p "$BASE/web"; cp -f "$TMP/repo/web/index.html" "$BASE/web/"; cp -f "$TMP/repo/web/app.js" "$BASE/web/"; cp -f "$TMP/repo/web/style.css" "$BASE/web/"
chmod 755 "$BASE/server.py" "$BASE/drops_tracker.py"; systemctl restart twitch-pi.service
echo "TwitchPi atualizado. Backup: $B"; systemctl --no-pager --full status twitch-pi.service
