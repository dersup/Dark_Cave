# serve_lan.ps1 - build for web and serve on the local subnet

param (
    [int]$PORT = 8080
)

$ErrorActionPreference = "Stop"

$GAME_DIR  = Split-Path -Parent $MyInvocation.MyCommand.Path
$BUILD_DIR = Join-Path $GAME_DIR "build\web"

# Activate the project venv
$VENV_ACTIVATE = Join-Path $GAME_DIR ".venv1\Scripts\Activate.ps1"
if (Test-Path $VENV_ACTIVATE) {
    & $VENV_ACTIVATE
} else {
    Write-Host "ERROR: venv not found at $VENV_ACTIVATE" -ForegroundColor Red
    exit 1
}

# Force UTF-8 file reads so pygbag doesn't choke on non-ASCII bytes
$env:PYTHONUTF8 = "1"

Write-Host "=== Dark Cave - LAN Web Server ==="
Write-Host ""

# Check pygbag
python -m pygbag --version 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing pygbag..."
    pip install pygbag -q
}

# Get local IP
try {
    $LOCAL_IP = (python -c @"
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.connect(('8.8.8.8', 80))
    print(s.getsockname()[0])
finally:
    s.close()
"@).Trim()
} catch {
    $LOCAL_IP = "localhost"
}

# Open a firewall rule so other LAN devices can reach the server.
# Requires an elevated (admin) shell - silently skipped if not admin.
$ruleName = "DarkCave-LAN-$PORT"
try {
    $existing = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
    if (-not $existing) {
        New-NetFirewallRule -DisplayName $ruleName `
            -Direction Inbound -Protocol TCP -LocalPort $PORT `
            -Action Allow -Profile Private | Out-Null
        Write-Host "Firewall rule '$ruleName' created for port $PORT."
    }
} catch {
    Write-Host "(Could not add firewall rule - run as admin if LAN clients can't connect.)"
}

Write-Host ""
Write-Host "Serving on:"
Write-Host "  http://localhost:$PORT"
Write-Host "  http://$($LOCAL_IP):$PORT   (share this with others on your LAN)"
Write-Host ""
Write-Host "Press Ctrl+C to stop."
Write-Host ""

# Register the .wasm MIME type so the browser accepts WebAssembly files.
# Requires admin - silently skipped if not elevated.

foreach ($ext in @(".js", ".mjs",".wasm")) {
    try {
        if (-not (Test-Path "HKLM:\SOFTWARE\Classes\$ext")) {
            New-Item -Path "HKLM:\SOFTWARE\Classes\$ext" -Force | Out-Null
        }
        Set-ItemProperty -Path "HKLM:\SOFTWARE\Classes\$ext" `
            -Name "Content Type" -Value "application/javascript"
        Write-Host "Registered $ext MIME type."
    } catch {
        Write-Host "(Could not set $ext MIME - run as admin if JS still fails.)"
    }
}
# Let pygbag build and serve in one step - generates index.html from
# its template and starts the dev server on all interfaces.
Set-Location $GAME_DIR
python -m pygbag --bind $LOCAL_IP --port $PORT --disable-sound-format-error $GAME_DIR