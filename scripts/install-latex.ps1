$ErrorActionPreference = "Stop"

$downloadPage = "https://miktex.org/download"
$tempDir = Join-Path $env:TEMP "jianli-creator-miktex"
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null

Write-Output "Resolving MiKTeX installer URL from $downloadPage ..."
$html = (Invoke-WebRequest -Uri $downloadPage -UseBasicParsing -TimeoutSec 30).Content
$pattern = '/download/ctan/systems/win32/miktex/setup/windows-x64/basic-miktex-[^"'' ]+-x64\.exe'
$match = [regex]::Match($html, $pattern)

if (-not $match.Success) {
    throw "Could not find the Basic MiKTeX installer link on the official download page."
}

$installerUrl = "https://miktex.org$($match.Value)"
$installerPath = Join-Path $tempDir ([System.IO.Path]::GetFileName($installerUrl))

Write-Output "Downloading MiKTeX installer..."
Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing -TimeoutSec 1800

Write-Output "Running private unattended MiKTeX installation..."
& $installerPath --unattended --private

$candidates = @(
    "$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin\x64\xelatex.exe",
    "$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe",
    "$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin\xelatex.exe",
    "$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin\pdflatex.exe"
)

foreach ($candidate in $candidates) {
    if (Test-Path $candidate) {
        Write-Output "Detected LaTeX engine at $candidate"
        exit 0
    }
}

throw "MiKTeX installation finished but no LaTeX engine was detected."
