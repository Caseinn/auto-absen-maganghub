#!/usr/bin/env bash
# Pasang jadwal cron Auto Absen MagangHub (Linux/VPS).
# Jadwal dibaca dari CLOCK_IN_TIME di .env (format HH:MM, bawaan 16:00).
# Cara pakai: ./setup_cron.sh
set -euo pipefail

WORKDIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$WORKDIR/.env"
MARKER="# AutoAbsenMaganghub"
REMINDER_MARKER="# AutoAbsenMaganghubReminder"

# Nilai bawaan bila .env atau CLOCK_IN_TIME tidak ada.
HOUR="16"
MIN="00"

# Nilai bawaan pengingat bila .env atau REMINDER_TIMES tidak ada.
REMINDER_TIMES="16:00,21:00"

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

  # Ambil baris REMINDER_TIMES pertama yang tidak dikomentari.
  RLINE="$(grep -E '^[[:space:]]*REMINDER_TIMES[[:space:]]*=' "$ENV_FILE" | head -n 1 || true)"
  if [ -n "${RLINE:-}" ]; then
    RVALUE="$(echo "$RLINE" | cut -d= -f2- | tr -d '"' | tr -d "'" | xargs)"
    if [ -n "$RVALUE" ]; then
      REMINDER_TIMES="$RVALUE"
    fi
  fi
else
  echo "[WARN] .env tidak ditemukan, pakai jam 16:00 dan pengingat 16:00,21:00." >&2
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

# Susun satu baris cron pengingat untuk setiap jam di REMINDER_TIMES.
REMINDER_LINES=""
IFS=',' read -ra REMINDER_ITEMS <<< "$REMINDER_TIMES"
for ITEM in "${REMINDER_ITEMS[@]}"; do
  ITEM="$(echo "$ITEM" | xargs)"
  if [ -z "$ITEM" ]; then
    continue
  fi
  if [[ "$ITEM" =~ ^([0-9]{1,2}):([0-9]{2})$ ]]; then
    RH="$(printf '%02d' "$((10#${BASH_REMATCH[1]}))")"
    RM="$(printf '%02d' "$((10#${BASH_REMATCH[2]}))")"
    if [ "$((10#$RH))" -le 23 ] && [ "$((10#$RM))" -le 59 ]; then
      REMINDER_LINES+="$RM $RH * * * cd \"$WORKDIR\" && \"$PYTHON\" main.py remind >> \"$WORKDIR/absen.log\" 2>&1 $REMINDER_MARKER"$'\n'
    else
      echo "[WARN] REMINDER_TIMES '$ITEM' di luar rentang, dilewati." >&2
    fi
  else
    echo "[WARN] REMINDER_TIMES '$ITEM' tidak valid, dilewati." >&2
  fi
done

# Pasang idempoten: buang entri lama bertanda, lalu tambah yang baru.
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
(crontab -l 2>/dev/null || true) | grep -v "$MARKER" | sed '/^[[:space:]]*$/d' > "$TMP" || true
echo "$CRON_LINE" >> "$TMP"
if [ -n "$REMINDER_LINES" ]; then
  printf '%s' "$REMINDER_LINES" >> "$TMP"
fi
crontab "$TMP"

echo "[OK] Cron 'AutoAbsenMaganghub' terpasang: tiap hari $HOUR:$MIN."
echo "[OK] Cron pengingat terpasang untuk jam: $REMINDER_TIMES."
echo "Cek:    crontab -l"
echo "Log:    tail -f \"$WORKDIR/absen.log\""
echo "Hapus:  crontab -l | grep -v '$MARKER' | crontab -"
echo "Ulangi skrip ini setiap ganti CLOCK_IN_TIME atau REMINDER_TIMES."
