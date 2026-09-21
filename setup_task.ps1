$taskName = "AutoAbsenMaganghub"
$workDir = $PSScriptRoot
$scriptPath = Join-Path $PSScriptRoot "main.py"
$venvPython = Join-Path $workDir ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $pythonPath = $venvPython
} else {
    $pythonPath = (Get-Command python).Source
}

$clockInTime = [DateTime]"16:00:00"
$envFile = Join-Path $workDir ".env"
if (Test-Path $envFile) {
    foreach ($line in Get-Content $envFile) {
        if ($line -match '^\s*CLOCK_IN_TIME\s*=\s*"?\s*(\d{1,2}):(\d{2})\s*"?\s*$') {
            $clockInTime = [DateTime]"$($Matches[1]):$($Matches[2])"
            break
        }
    }
}

$action = New-ScheduledTaskAction -Execute $pythonPath -Argument "$scriptPath absen" -WorkingDirectory $workDir
$trigger = New-ScheduledTaskTrigger -Daily -At $clockInTime.TimeOfDay

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType S4U -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -WakeToRun

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force

Write-Host "[OK] Task '$taskName' berhasil dibuat: clock in setiap $($clockInTime.ToString('HH:mm'))"
Write-Host "Cek: Get-ScheduledTask -TaskName '$taskName'"
Write-Host "Hapus: Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"
