# StartLocalAssistant.ps1 - Simple Version
# Local Writing Assistant - Startup Script

param(
    [switch]$Force
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Local Writing Assistant - Startup" -ForegroundColor Cyan  
Write-Host "============================================================" -ForegroundColor Cyan

# Get paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)

Write-Host "Project directory: $ProjectRoot" -ForegroundColor Green
Set-Location $ProjectRoot

# Create directories
if (!(Test-Path ".logs")) { New-Item -ItemType Directory -Path ".logs" -Force | Out-Null }
if (!(Test-Path ".run")) { New-Item -ItemType Directory -Path ".run" -Force | Out-Null }

Write-Host "`n--------------------------------------------" -ForegroundColor Blue
Write-Host "Checking Dependencies" -ForegroundColor Blue
Write-Host "--------------------------------------------" -ForegroundColor Blue

# Check Python
try {
    $null = Get-Command python -ErrorAction Stop
    $pythonVersion = & python --version 2>&1
    Write-Host "✓ Python is available: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python is missing" -ForegroundColor Red
    Write-Host "  Install: winget install -e --id Python.Python.3.11" -ForegroundColor Yellow
    if (!$Force) { exit 1 }
}

# Check Java
try {
    $null = Get-Command java -ErrorAction Stop
    Write-Host "✓ Java is available" -ForegroundColor Green
} catch {
    Write-Host "✗ Java is missing" -ForegroundColor Red
    Write-Host "  Install: winget install -e --id EclipseAdoptium.Temurin.17.JDK" -ForegroundColor Yellow
    if (!$Force) { exit 1 }
}

# Check FFmpeg
try {
    $null = Get-Command ffmpeg -ErrorAction Stop
    Write-Host "✓ FFmpeg is available" -ForegroundColor Green
} catch {
    Write-Host "✗ FFmpeg is missing" -ForegroundColor Red
    Write-Host "  Install: winget install -e --id Gyan.FFmpeg" -ForegroundColor Yellow
    if (!$Force) { exit 1 }
}

Write-Host "`n--------------------------------------------" -ForegroundColor Blue
Write-Host "Setting up Python Environment" -ForegroundColor Blue  
Write-Host "--------------------------------------------" -ForegroundColor Blue

# Create venv
if (!(Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    & python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
}

# Activate venv
$activateScript = ".venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & $activateScript
    Write-Host "✓ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "✗ Activation script not found" -ForegroundColor Red
    exit 1
}

# Install requirements
if (Test-Path "server\requirements.txt") {
    Write-Host "Installing Python packages..." -ForegroundColor Yellow
    & python -m pip install -U pip wheel
    & python -m pip install -r server\requirements.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Python dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✗ Requirements file not found" -ForegroundColor Red
    exit 1
}

Write-Host "`n--------------------------------------------" -ForegroundColor Blue
Write-Host "Environment Configuration" -ForegroundColor Blue
Write-Host "--------------------------------------------" -ForegroundColor Blue

# Create .env file
if (!(Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        
        # Generate random token
        $chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        $token = ""
        for ($i = 0; $i -lt 32; $i++) {
            $token += $chars[(Get-Random -Maximum $chars.Length)]
        }
        
        # Replace token in .env
        $content = Get-Content ".env" -Raw
        $content = $content -replace "your-secure-random-token-here", $token
        Set-Content ".env" $content
        
        Write-Host "✓ .env file created with API token" -ForegroundColor Green
    } else {
        Write-Host "✗ .env.example not found" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
}

Write-Host "`n--------------------------------------------" -ForegroundColor Blue
Write-Host "Downloading AI Models" -ForegroundColor Blue
Write-Host "--------------------------------------------" -ForegroundColor Blue

if (Test-Path "server\scripts\download_models.py") {
    Write-Host "Downloading models (this may take a few minutes)..." -ForegroundColor Yellow
    & python server\scripts\download_models.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ AI models downloaded" -ForegroundColor Green
    } else {
        Write-Host "⚠ Model download had issues, continuing..." -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠ Model download script not found" -ForegroundColor Yellow
}

Write-Host "`n--------------------------------------------" -ForegroundColor Blue
Write-Host "Starting Server" -ForegroundColor Blue
Write-Host "--------------------------------------------" -ForegroundColor Blue

# Start server
Write-Host "Starting Local Writing Assistant server..." -ForegroundColor Yellow

$logFile = ".logs\uvicorn.log"
$pidFile = ".run\uvicorn.pid"

# Start in background
$process = Start-Process -FilePath "python" -ArgumentList @("-m", "uvicorn", "server.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload") -NoNewWindow -PassThru -RedirectStandardOutput $logFile -RedirectStandardError $logFile

# Save PID
$process.Id | Out-File $pidFile -Encoding ASCII

Write-Host "✓ Server started (PID: $($process.Id))" -ForegroundColor Green

# Wait and test
Start-Sleep -Seconds 5

try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get -TimeoutSec 10
    if ($response.ok) {
        Write-Host "✓ Server is healthy and responding" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠ Server started but health check failed" -ForegroundColor Yellow
    Write-Host "Check logs at: $logFile" -ForegroundColor Yellow
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Local Writing Assistant Started Successfully!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Write-Host "`n🚀 Services:" -ForegroundColor Green
Write-Host "   Server: http://127.0.0.1:8000" -ForegroundColor White
Write-Host "   API Docs: http://127.0.0.1:8000/docs" -ForegroundColor White

Write-Host "`n📁 Files:" -ForegroundColor Blue
Write-Host "   Logs: .logs\uvicorn.log" -ForegroundColor White
Write-Host "   Config: .env" -ForegroundColor White

Write-Host "`n🔧 Next Steps:" -ForegroundColor Magenta
Write-Host "   1. Load Chrome extension from /extension" -ForegroundColor White
Write-Host "   2. Chrome: Extensions → Developer Mode → Load unpacked" -ForegroundColor White
Write-Host "   3. Select the 'extension' folder" -ForegroundColor White
Write-Host "   4. Configure with API token (in .env file)" -ForegroundColor White

Write-Host "`n⚡ Commands:" -ForegroundColor Yellow
Write-Host "   Stop: .\scripts\windows\StopLocalAssistant.ps1" -ForegroundColor White

# Open browser
Write-Host "`nOpening API documentation..." -ForegroundColor Cyan
Start-Process "http://127.0.0.1:8000/docs"

Write-Host "`n✅ Local Writing Assistant is ready!" -ForegroundColor Green
