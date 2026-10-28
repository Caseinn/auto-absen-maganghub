# Helper bersama untuk setup_task.ps1 dan setup_reminder.ps1.

function Get-PythonPath {
    param([string]$WorkDir)
    $venvPython = Join-Path $WorkDir ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        return $venvPython
    }
    return (Get-Command python).Source
}

function Get-EnvValue {
    param(
        [string]$EnvFile,
        [string]$Key
    )
    if (-not (Test-Path $EnvFile)) {
        return $null
    }
    $pattern = '^\s*' + [regex]::Escape($Key) + '\s*=\s*"?\s*(.*?)\s*"?\s*$'
    foreach ($line in Get-Content $EnvFile) {
        if ($line -match $pattern) {
            return $Matches[1]
        }
    }
    return $null
}

function ConvertTo-TimeOfDay {
    param([string]$Value)
    if ($Value -match '^\s*(\d{1,2}):(\d{2})\s*$') {
        $hour = [int]$Matches[1]
        $minute = [int]$Matches[2]
        if ($hour -ge 0 -and $hour -le 23 -and $minute -ge 0 -and $minute -le 59) {
            return New-TimeSpan -Hours $hour -Minutes $minute
        }
    }
    return $null
}
