#!/usr/bin/env bash
# Pasang jadwal cron Auto Absen MagangHub (Linux/VPS).
# Jadwal dibaca dari CLOCK_IN_TIME di .env (format HH:MM, bawaan 16:00).
# Cara pakai: ./setup_cron.sh
set -euo pipefail

WORKDIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$WORKDIR/.env"
MARKER="# AutoAbsenMaganghub"

# Nilai bawaan bila .env atau CLOCK_IN_TIME tidak ada.
HOUR="16"
MIN="00"

if [ -f "$ENV_FILE" ]; then
  # Ambil baris CLOCK_IN_TIME pertama yang tidak dikomentari.
  LINE="$(grep -E '^[[:space:]]*CLOCK_IN_TIME[[:space:]]*=' "$ENV_FILE" | head -n 1 || true)"
  if [ -n "${LINE:-}" ]; then
    # Buang nama variabel, tanda kutip, dan spasi di sekitar nilai.
    VALUE="$(echo "$LINE" | cut -d= -f2- | tr -d '"' | tr -d "'" | xargs)"
    if [[ "$VALUE" =~ ^([0-9]{1,2}):([0-9]{2})$ ]]; then
      HOUR="$(printf '%02d' "$((10#${BASH_REMATCH[1]}))")"
      MIN="$(printf '%02d' "$((10#${BASH_REMATCH[2]}))")"
    else
      echo "[WARN] CLOCK_IN_TIME='$VALUE' tidak valid, pakai 16:00." >&2
      HOUR="16"
      MIN="00"
    fi
  fi
else
  echo "[WARN] .env tidak ditemukan, pakai jam 16:00." >&2
fi

if [ "$((10#$HOUR))" -gt 23 ] || [ "$((10#$MIN))" -gt 59 ]; then
  echo "[WARN] Jam $HOUR:$MIN di luar rentang, pakai 16:00." >&2
  HOUR="16"
  MIN="00"
fi

# Python dari .venv bila ada, kalau tidak pakai python3 dari PATH.
if [ -x "$WORKDIR/.venv/bin/python" ]; then
  PYTHON="$WORKDIR/.venv/bin/python"
else
  PYTHON="$(command -v python3 || command -v python || true)"
fi
if [ -z "${PYTHON:-}" ]; then
  echo "[FAIL] python3 tidak ditemukan. Pasang Python 3.10+ dulu." >&2
  exit 1
fi

if ! command -v crontab >/dev/null 2>&1; then
  echo "[FAIL] Perintah 'crontab' tidak ditemukan. Pasang cron dulu (misal: sudo apt install cron)." >&2
  exit 1
fi

# Ingatkan bila zona waktu bukan WIB (tidak diganti otomatis).
if command -v timedatectl >/dev/null 2>&1; then
  TZ_NOW="$(timedatectl show --property=Timezone --value 2>/dev/null || true)"
  if [ -n "${TZ_NOW:-}" ] && [ "$TZ_NOW" != "Asia/Jakarta" ]; then
    echo "[WARN] Zona waktu sekarang $TZ_NOW, bukan Asia/Jakarta." >&2
    echo "       Jalankan: sudo timedatectl set-timezone Asia/Jakarta" >&2
  fi
fi

CRON_LINE="$MIN $HOUR * * * cd \"$WORKDIR\" && \"$PYTHON\" main.py absen >> \"$WORKDIR/absen.log\" 2>&1 $MARKER"

# Pasang idempoten: buang entri lama bertanda, lalu tambah yang baru.
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
(crontab -l 2>/dev/null || true) | grep -v "$MARKER" | sed '/^[[:space:]]*$/d' > "$TMP" || true
echo "$CRON_LINE" >> "$TMP"
crontab "$TMP"

echo "[OK] Cron 'AutoAbsenMaganghub' terpasang: tiap hari $HOUR:$MIN."
echo "Cek:    crontab -l"
echo "Log:    tail -f \"$WORKDIR/absen.log\""
echo "Hapus:  crontab -l | grep -v '$MARKER' | crontab -"
echo "Ulangi skrip ini setiap ganti CLOCK_IN_TIME."
