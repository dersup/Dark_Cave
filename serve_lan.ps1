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
try {
    if (-not (Test-Path "HKLM:\SOFTWARE\Classes\.wasm")) {
        New-Item -Path "HKLM:\SOFTWARE\Classes\.wasm" -Force | Out-Null
    }
    Set-ItemProperty -Path "HKLM:\SOFTWARE\Classes\.wasm" `
        -Name "Content Type" -Value "application/wasm"
    Write-Host "Registered .wasm MIME type."
} catch {
    # Fallback: register for current user only (no admin needed)
    try {
        if (-not (Test-Path "HKCU:\SOFTWARE\Classes\.wasm")) {
            New-Item -Path "HKCU:\SOFTWARE\Classes\.wasm" -Force | Out-Null
        }
        Set-ItemProperty -Path "HKCU:\SOFTWARE\Classes\.wasm" `
            -Name "Content Type" -Value "application/wasm"
        Write-Host "Registered .wasm MIME type (current user)."
    } catch {
        Write-Host "(Could not register .wasm MIME type - run as admin if game won't load.)"
    }
}

# Let pygbag build and serve in one step - generates index.html from
# its template and starts the dev server on all interfaces.
Set-Location $GAME_DIR
python -m pygbag --port $PORT --bind 0.0.0.0 --disable-sound-format-error .