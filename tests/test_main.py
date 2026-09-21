"""Tests for attendance CLI logic. No network access."""

import re
from pathlib import Path

import requests

import app.commands as commands
import app.utils.net as netmod
from app.api.client import ApiError
from app.commands import cmd_dry_run, cmd_status, invalid_days, should_skip, validate_env
from app.models.attendance import AttendanceService
from app.models.attendance import DailyLog
from app.utils.net import net_msg, retryable, with_retry
from app.utils.time import date_str, now_wib


def testretryable_network_errors():
    assert retryable(requests.exceptions.ConnectionError("putus"))
    assert retryable(requests.exceptions.Timeout("lambat"))


def testretryable_server_errors():
    assert retryable(ApiError(500, "salah server"))
    assert retryable(ApiError(503, "sibuk"))


def test_not_retryable_errors():
    assert not retryable(ApiError(409, "sudah absen"))
    assert not retryable(ApiError(401, "token salah"))
    assert not retryable(ValueError("lainnya"))


def testwith_retry_succeeds_after_flaky_attempts(monkeypatch):
    monkeypatch.setattr(netmod, "RETRY_DELAY", 0)
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise requests.exceptions.ConnectionError("blip")
        return "ok"

    assert with_retry("Tes", flaky) == "ok"
    assert len(calls) == 3


def testwith_retry_gives_up_after_max_attempts(monkeypatch):
    monkeypatch.setattr(netmod, "RETRY_DELAY", 0)
    calls = []

    def always_fail():
        calls.append(1)
        raise requests.exceptions.Timeout("mati")

    try:
        with_retry("Tes", always_fail)
        raise AssertionError("seharusnya melempar")
    except requests.exceptions.Timeout:
        pass
    assert len(calls) == netmod.MAX_ATTEMPTS


def testwith_retry_skips_retry_for_final_errors(monkeypatch):
    monkeypatch.setattr(netmod, "RETRY_DELAY", 0)
    calls = []

    def fail_409():
        calls.append(1)
        raise ApiError(409, "sudah absen")

    try:
        with_retry("Tes", fail_409)
        raise AssertionError("seharusnya melempar")
    except ApiError:
        pass
    assert len(calls) == 1


def testnet_msg():
    assert net_msg(requests.exceptions.Timeout("lambat")) == "[FAIL] Koneksi timeout."
    assert net_msg(requests.exceptions.ConnectionError("putus")) == (
        "[FAIL] Gagal terhubung ke server. Cek koneksi internet."
    )


def testshould_skip_today(monkeypatch):
    today_name = commands.HARI[now_wib().weekday()]
    monkeypatch.setattr(commands.settings, "hari_libur", today_name)
    assert should_skip() is True


def testshould_skip_case_insensitive(monkeypatch):
    today_name = commands.HARI[now_wib().weekday()]
    monkeypatch.setattr(commands.settings, "hari_libur", today_name.lower())
    assert should_skip() is True
    monkeypatch.setattr(commands.settings, "hari_libur", today_name.upper())
    assert should_skip() is True


def test_should_not_skip_other_day(monkeypatch):
    monkeypatch.setattr(commands.settings, "hari_libur", "TidakAdaHari")
    assert should_skip() is False


def _fill_env(monkeypatch, **overrides):
    values = {
        "siapkerja_username": "user",
        "siapkerja_password": "sandi",
        "activity_log": "aktivitas",
        "lesson_learned": "pelajaran",
        "obstacles": "kendala",
    }
    values.update(overrides)
    for key, value in values.items():
        monkeypatch.setattr(commands.settings, key, value)


def testvalidate_env_complete(monkeypatch, capsys):
    _fill_env(monkeypatch)
    assert validate_env() is True


def testvalidate_env_missing(monkeypatch, capsys):
    _fill_env(monkeypatch, obstacles="")
    assert validate_env() is False
    assert "OBSTACLES" in capsys.readouterr().out


def test_daily_log_parsing():
    log_entry = DailyLog({
        "id": 1,
        "date": "2026-09-21",
        "clock_in": "16:00",
        "activity_log": "Magang hari ini",
        "lesson_learned": "Belajar hal baru",
        "obstacles": "Tidak ada",
    })
    assert log_entry.id == 1
    assert log_entry.date == "2026-09-21"
    assert log_entry.clock_in == "16:00"
    assert log_entry.activity_log == "Magang hari ini"
    assert log_entry.lesson_learned == "Belajar hal baru"
    assert log_entry.obstacles == "Tidak ada"


def test_daily_log_missing_optional_fields():
    log_entry = DailyLog({"id": 2, "date": "2026-09-21"})
    assert log_entry.clock_in is None
    assert log_entry.activity_log is None
    assert log_entry.lesson_learned is None
    assert log_entry.obstacles is None


def test_log_writes_to_console_and_file(tmp_path, monkeypatch, capsys):
    import app.utils.log as logmod

    monkeypatch.setattr(logmod, "LOG_FILE", tmp_path / "test.log")
    logmod.log("[OK] Tes tulis")
    assert "[OK] Tes tulis" in capsys.readouterr().out
    content = (tmp_path / "test.log").read_text(encoding="utf-8")
    assert "[OK] Tes tulis" in content
    assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", content)


def test_log_never_raises(monkeypatch, capsys):
    import app.utils.log as logmod

    monkeypatch.setattr(logmod, "LOG_FILE", Path("/jalur-tidak-ada-xyz/test.log"))
    logmod.log("[OK] Tes aman")
    assert "[OK] Tes aman" in capsys.readouterr().out


def test_invalid_days_empty(monkeypatch):
    monkeypatch.setattr(commands.settings, "hari_libur", "")
    assert invalid_days() == []


def test_invalid_days_valid(monkeypatch):
    monkeypatch.setattr(commands.settings, "hari_libur", "Sabtu,minggu")
    assert invalid_days() == []


def test_invalid_days_typo(monkeypatch):
    monkeypatch.setattr(commands.settings, "hari_libur", "Sabtu,Saptu,Foo")
    assert invalid_days() == ["Saptu", "Foo"]


def test_attendance_payload_shape():
    payload = AttendanceService.attendance_payload("2026-09-21")
    assert payload["date"] == "2026-09-21"
    assert payload["status"] == "PRESENT"
    assert set(payload) == {"date", "status", "activity_log", "lesson_learned", "obstacles"}


def test_date_str_format():
    assert re.match(r"\d{4}-\d{2}-\d{2}", date_str(3))
    assert date_str(0) == date_str()


def test_cmd_dry_run_success(monkeypatch, capsys):
    _fill_env(monkeypatch)
    assert cmd_dry_run() == 0
    assert "PRESENT" in capsys.readouterr().out


def test_cmd_dry_run_missing_env(monkeypatch, capsys):
    _fill_env(monkeypatch, obstacles="")
    assert cmd_dry_run() == 1


class FakeService:
    """Stub attendance service backed by a dict, no network."""

    def __init__(self, entries):
        self.entries = entries

    def get_log(self, date):
        return self.entries.get(date)


def test_status_single_day_detailed(capsys):
    entry = DailyLog({
        "id": 1,
        "date": date_str(0),
        "clock_in": "16:00",
        "activity_log": "Magang",
        "lesson_learned": "Belajar",
        "obstacles": "Tidak ada",
    })
    assert cmd_status(FakeService({date_str(0): entry})) == 0
    out = capsys.readouterr().out
    assert "Pelajaran:  Belajar" in out
    assert "Kendala:    Tidak ada" in out


def test_status_single_day_missing(capsys):
    assert cmd_status(FakeService({})) == 0
    assert "Belum ada absen" in capsys.readouterr().out


def test_status_empty_fields_explained(capsys):
    entry = DailyLog({"id": 1, "date": date_str(0)})
    assert cmd_status(FakeService({date_str(0): entry})) == 0
    out = capsys.readouterr().out
    assert "tidak tercatat" in out
    assert "  -" not in out


def test_get_log_matches_requested_date():
    svc = AttendanceService()

    class FakeApiClient:
        def get(self, path, params=None):
            return {"data": [
                {"id": 9, "date": "2026-09-21"},
                {"id": 8, "date": "2026-09-18"},
            ]}

    svc._client = FakeApiClient()
    assert svc.get_log("2026-09-18").id == 8
    assert svc.get_log("2026-09-20") is None


def test_get_log_searches_next_pages():
    svc = AttendanceService()
    calls = []

    class PagedApiClient:
        def get(self, path, params=None):
            calls.append((params or {}).get("page", 1))
            if (params or {}).get("page", 1) == 1:
                return {"data": [{"id": 9, "date": "2026-09-21"}], "total": 3}
            if (params or {}).get("page") == 2:
                return {"data": [{"id": 8, "date": "2026-09-18"}], "total": 3}
            return {"data": [], "total": 3}

    svc._client = PagedApiClient()
    assert svc.get_log("2026-09-18").id == 8
    assert calls == [1, 2]


def test_get_log_single_page_short_circuits():
    svc = AttendanceService()
    calls = []

    class SinglePageApiClient:
        def get(self, path, params=None):
            calls.append((params or {}).get("page", 1))
            return {"data": [{"id": 9, "date": "2026-09-21"}], "total": 1}

    svc._client = SinglePageApiClient()
    assert svc.get_log("2026-09-20") is None
    assert calls == [1]


def test_status_history_readable(capsys):
    svc = FakeService({
        date_str(0): DailyLog({"id": 1, "date": date_str(0), "clock_in": "16:00"}),
        date_str(2): DailyLog({"id": 2, "date": date_str(2)}),
    })
    assert cmd_status(svc, days=3) == 0
    out = capsys.readouterr().out
    assert f"[OK] {date_str(0)}  Hadir" in out
    assert f"[OK] {date_str(1)}  Tidak Hadir" in out
    assert f"[OK] {date_str(2)}  Hadir" in out
    assert "tercatat" not in out
