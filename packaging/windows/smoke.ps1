# Windows smoke: install, run, check health, persist paused job, restart, uninstall.
param([Parameter(Mandatory=$true)][string]$Installer)
$ErrorActionPreference = "Stop"
$port = 18765
$data = Join-Path $env:RUNNER_TEMP "transcript-studio-ci-data"
$installDir = Join-Path $env:RUNNER_TEMP "TranscriptStudioInstalled"
New-Item -ItemType Directory -Force $data | Out-Null
$installed = $false

function Run-Server([string]$exe) {
    $script:process = Start-Process -FilePath $exe -ArgumentList @(
        "--no-browser", "--port", "$port", "--data-dir", $data
    ) -PassThru -WindowStyle Hidden
    for ($n=0; $n -lt 90; $n++) {
        if ($script:process.HasExited) { throw "App exited with $($script:process.ExitCode)" }
        try {
            $health = Invoke-RestMethod "http://127.0.0.1:$port/api/health" -TimeoutSec 1
            if ($health.ok -eq $true) { return }
        } catch { Start-Sleep -Milliseconds 750 }
    }
    throw "Health endpoint never became ready"
}
function Stop-Server() {
    if ($script:process -and !$script:process.HasExited) {
        Stop-Process -Id $script:process.Id -Force
        $script:process.WaitForExit()
    }
}
try {
    $p = Start-Process -FilePath $Installer -ArgumentList @(
        "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART",
        "/DIR=$installDir"
    ) -Wait -PassThru
    if ($p.ExitCode -ne 0) { throw "Installer exited $($p.ExitCode)" }
    $exe = Join-Path $installDir "TranscriptStudio.exe"
    if (!(Test-Path $exe)) { throw "Missing installed executable" }
    $installed = $true
    # Create a PAUSED job via the Python test environment: no requests to YouTube.
    $env:TS_TEST_DATA_DIR = $data
    python -c "import os;from pathlib import Path;from transcript_studio.storage import Store;s=Store(Path(os.environ['TS_TEST_DATA_DIR'])/'library.sqlite3');j=s.create_job('https://www.youtube.com/@dummy/videos',['es'],{'max_videos':1});s.set_status(j['id'],'paused');print(j['id'])"
    if ($LASTEXITCODE -ne 0) { throw "Could not create smoke fixture" }
    Run-Server $exe
    $jobs = Invoke-RestMethod "http://127.0.0.1:$port/api/jobs"
    if (@($jobs | Where-Object status -EQ "paused").Count -lt 1) { throw "Paused job missing" }
    Stop-Server
    Run-Server $exe
    $jobs = Invoke-RestMethod "http://127.0.0.1:$port/api/jobs"
    if (@($jobs | Where-Object status -EQ "paused").Count -lt 1) { throw "Data not persistent after restart" }
    Stop-Server
    $uninstaller = Join-Path $installDir "unins000.exe"
    if (!(Test-Path $uninstaller)) { throw "Missing uninstaller" }
    $u = Start-Process -FilePath $uninstaller -ArgumentList @(
        "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"
    ) -Wait -PassThru
    if ($u.ExitCode -ne 0) { throw "Uninstaller exited $($u.ExitCode)" }
    if (!(Test-Path (Join-Path $data "library.sqlite3"))) {
        throw "Uninstall destroyed user data"
    }
    Write-Host "PASS: installation, local health, data after restart, uninstall preserves data"
} finally {
    Stop-Server
}
