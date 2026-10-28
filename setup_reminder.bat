@echo off
rem Klik dua kali untuk pasang Task Scheduler AutoAbsenMaganghubReminder.
rem Skrip ini minta akses Administrator lalu menjalankan setup_reminder.ps1.
setlocal

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Meminta akses Administrator...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_reminder.ps1"
if %errorlevel% neq 0 (
    echo [FAIL] Pendaftaran tugas gagal.
) else (
    echo Cek:   Get-ScheduledTask -TaskName 'AutoAbsenMaganghubReminder'
    echo Hapus: Unregister-ScheduledTask -TaskName 'AutoAbsenMaganghubReminder' -Confirm:$false
)
pause
