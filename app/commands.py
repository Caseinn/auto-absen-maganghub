"""CLI command handlers for absen, status, dry-run, and doctor."""

import json
import os
import subprocess

from app.config import settings
from app.models.attendance import AttendanceService
from app.utils.log import log
from app.utils.net import network_guard, with_retry
from app.utils.telegram import notify
from app.utils.time import date_str, now_wib, today_str

HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
TASK_NAME = "AutoAbsenMaganghub"


def should_skip() -> bool:
    """Return True if today is listed in HARI_LIBUR."""
    today_name = HARI[now_wib().weekday()]
    for d in settings.hari_libur.split(","):
        if d.strip().casefold() == today_name.casefold():
            return True
    return False


def invalid_days() -> list[str]:
    """Return HARI_LIBUR entries that match no known day name."""
    known = {d.casefold() for d in HARI}
    bad = []
    for d in settings.hari_libur.split(","):
        name = d.strip()
        if name and name.casefold() not in known:
            bad.append(name)
    return bad


def validate_env():
    """Return True if required env vars are set, else log error."""
    missing = []
    if not settings.siapkerja_username:
        missing.append("SIAPKERJA_USERNAME")
    if not settings.siapkerja_password:
        missing.append("SIAPKERJA_PASSWORD")
    if not settings.activity_log:
        missing.append("ACTIVITY_LOG")
    if not settings.lesson_learned:
        missing.append("LESSON_LEARNED")
    if not settings.obstacles:
        missing.append("OBSTACLES")
    if missing:
        log(f"[FAIL] Variabel berikut wajib diisi di .env: {', '.join(missing)}")
        return False
    return True


@network_guard
def cmd_absen(svc: AttendanceService) -> int:
    """Send attendance for today. Return 0 on success, 1 on failure."""
    if not validate_env():
        notify("[FAIL] Konfigurasi tidak lengkap. Cek absen.log untuk detail.")
        return 1
    unknown = invalid_days()
    if unknown:
        msg = f"[FAIL] Nama hari tidak dikenal di HARI_LIBUR: {', '.join(unknown)}"
        log(msg)
        notify(msg)
        return 1
    if should_skip():
        log("[SKIP] Hari ini libur, absen dilewati.")
        return 0
    try:
        with_retry("Absen", lambda: svc.clock_in(today_str()))
    except Exception as e:
        if getattr(e, "status_code", None) == 409:
            msg = "[OK] Sudah absen hari ini."
            log(msg)
            notify(msg)
            return 0
        msg = f"[FAIL] {e}"
        log(msg)
        notify(msg)
        return 1
    msg = f"[OK] Absen {today_str()} berhasil terkirim."
    log(msg)
    notify(msg)
    return 0


def cmd_dry_run() -> int:
    """Show the payload absen would send, without network. Return exit code."""
    if not validate_env():
        return 1
    payload = AttendanceService.attendance_payload(today_str())
    log(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


@network_guard
def cmd_status(svc: AttendanceService, days: int = 1) -> int:
    """Show attendance status. Return 0 on success, 1 on failure.

    Args:
        svc: Authenticated attendance service.
        days: How many days back to show. 1 means detailed today view.
    """
    if days == 1:
        entry = svc.get_log(today_str())
        if not entry:
            log(f"Belum ada absen pada {today_str()}")
            return 0
        log(f"Status: {entry.date}")
        log(f"  Aktivitas:  {entry.activity_log or 'tidak tercatat'}")
        log(f"  Pelajaran:  {entry.lesson_learned or 'tidak tercatat'}")
        log(f"  Kendala:    {entry.obstacles or 'tidak tercatat'}")
        return 0
    for ago in range(days):
        date = date_str(ago)
        entry = svc.get_log(date)
        if entry:
            log(f"[OK] {date}  Hadir")
        else:
            log(f"[OK] {date}  Tidak Hadir")
    return 0


def cmd_doctor() -> int:
    """Run setup self-checks. Return 0 if all pass, 1 otherwise."""
    failed = 0

    if validate_env():
        log("[OK] Variabel wajib lengkap.")
    else:
        failed += 1

    unknown = invalid_days()
    if not unknown:
        log("[OK] Nama hari di HARI_LIBUR valid.")
    else:
        log(f"[FAIL] Nama hari tidak dikenal: {', '.join(unknown)}")
        failed += 1

    try:
        svc = AttendanceService()
        with_retry("Login", svc.login)
        log("[OK] Login berhasil.")
    except Exception as e:
        log(f"[FAIL] Login gagal: {e}")
        failed += 1

    if settings.telegram_bot_token and settings.telegram_chat_id:
        notify("Notifikasi Telegram aktif. (Pesan tes dari doctor.)")
        log("[OK] Pesan tes terkirim, cek HP Anda.")
    else:
        log("[SKIP] Notifikasi Telegram belum dikonfigurasi.")

    if os.name == "nt":
        try:
            r = subprocess.run(
                ["schtasks", "/query", "/tn", TASK_NAME],
                capture_output=True,
            )
            if r.returncode == 0:
                log("[OK] Tugas scheduler terdaftar.")
            else:
                log(f"[FAIL] Tugas scheduler '{TASK_NAME}' tidak ditemukan.")
                failed += 1
        except OSError as e:
            log(f"[FAIL] Cek scheduler gagal: {e}")
            failed += 1
    else:
        log("[SKIP] Cek scheduler hanya di Windows.")

    if failed:
        log(f"[FAIL] Doctor: {failed} pemeriksaan gagal.")
        return 1
    log("[OK] Doctor: semua pemeriksaan lolos.")
    return 0
