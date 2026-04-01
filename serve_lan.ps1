# serve_lan.ps1 — build for web and serve on the local subnet

$ErrorActionPreference = "Stop"

$GAME_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$BUILD_DIR = Join-Path $GAME_DIR "build\web"

# Default port = 8080 if not provided
param (
    [int]$PORT = 8080
)

Write-Host "=== Dark Cave — LAN Web Server ==="
Write-Host ""

# Check pygbag
try {
    python -m pygbag --version *> $null
} catch {
    Write-Host "Installing pygbag..."
    pip install pygbag --break-system-packages -q
}

Write-Host "Building web bundle (this takes ~30 s first time)..."
Set-Location $GAME_DIR
python -m pygbag --build main.py

Write-Host ""
Write-Host "Build complete."
Write-Host ""

# Get local IP
try {
    $LOCAL_IP = python -c @"
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.connect(('8.8.8.8', 80))
    print(s.getsockname()[0])
finally:
    s.close()
"@
} catch {
    $LOCAL_IP = "localhost"
}

Write-Host "Serving on:"
Write-Host "  http://localhost:$PORT"
Write-Host "  http://$LOCAL_IP`:$PORT   ← share this with others on your LAN"
Write-Host ""
Write-Host "Press Ctrl+C to stop."
Write-Host ""

Set-Location $BUILD_DIR
python -m http.server $PORT
