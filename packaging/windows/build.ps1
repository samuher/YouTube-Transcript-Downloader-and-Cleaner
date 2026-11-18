# Build a local, unsigned Windows installer. Never publish automatically.
$ErrorActionPreference = "Stop"
Set-Location (Resolve-Path (Join-Path $PSScriptRoot "../.."))
$version = python -c "import transcript_studio; print(transcript_studio.__version__)"
$pyInstallerArgs = @(
    "--noconfirm", "--clean", "--onedir", "--name", "TranscriptStudio",
    "--collect-all", "yt_dlp_ejs", "--collect-submodules", "yt_dlp",
    "--add-data", "src/transcript_studio/static;transcript_studio/static",
    "packaging/windows/launcher.py"
)
python -m PyInstaller @pyInstallerArgs
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }
$compiler = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue
if ($compiler) { $iscc = $compiler.Source }
else {
    $iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
    if (!(Test-Path $iscc)) { $iscc = "$env:ProgramFiles\Inno Setup 6\ISCC.exe" }
}
if (!(Test-Path $iscc)) { throw "Inno Setup 6 compiler (ISCC.exe) not found" }
& $iscc "/DAppVersion=$version" "packaging/windows/installer.iss"
if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed" }
Get-ChildItem "dist/installer/*.exe" | Get-FileHash -Algorithm SHA256 | Format-Table
