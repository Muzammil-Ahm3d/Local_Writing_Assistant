# StartLocalAssistant.ps1
# Local Writing Assistant - Startup Script  
# Single-click start with health checks

param(
    [switch]$Verbose,
    [switch]$SkipBrowser,
    [switch]$Force
)

$ErrorActionPreference = "Continue"
$VerbosePreference = if ($Verbose) { "Continue" } else { "SilentlyContinue" }

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)

# Get script directory and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)

# Colors for output
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    
    $colors = @{
        "Red" = [ConsoleColor]::Red
        "Green" = [ConsoleColor]::Green  
        "Yellow" = [ConsoleColor]::Yellow
        "Blue" = [ConsoleColor]::Blue
        "Cyan" = [ConsoleColor]::Cyan
        "Magenta" = [ConsoleColor]::Magenta
        "White" = [ConsoleColor]::White
    }
    
    Write-Host $Message -ForegroundColor $colors[$Color]
}

function Write-Header {
    param([string]$Title)
    Write-ColorOutput "`n$('='*60)" "Cyan"
    Write-ColorOutput "$Title" "Cyan"
    Write-ColorOutput "$('='*60)" "Cyan"
}

function Write-Section {
    param([string]$Title)
    Write-ColorOutput "`n$('-'*40)" "Blue"
    Write-ColorOutput "$Title" "Blue"
    Write-ColorOutput "$('-'*40)" "Blue"
}

function Test-Port {
    param([int]$Port)
    try {
        $tcpObject = New-Object System.Net.Sockets.TcpClient
        $connect = $tcpObject.BeginConnect("127.0.0.1", $Port, $null, $null)
        $wait = $connect.AsyncWaitHandle.WaitOne(1000, $false)
        if ($wait) {
            $tcpObject.EndConnect($connect)
            $tcpObject.Close()
            return $true
        } else {
            $tcpObject.Close()
            return $false
        }
    } catch {
        return $false
    }
}

function Stop-ProcessByPort {
    param([int]$Port)
    try {
        $connections = netstat -ano | findstr ":$Port "
        foreach ($line in $connections) {
            if ($line -match '\s+(\d+)$') {
                $pid = $matches[1]
                Write-ColorOutput "Stopping process $pid using port $Port..." "Yellow"
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                Start-Sleep -Seconds 2
            }
        }
    } catch {
        Write-ColorOutput "Could not stop processes on port $Port" "Yellow"
    }
}

function Test-Dependency {
    param([string]$Command, [string]$Name, [string]$InstallHint)
    
    try {
        $null = Get-Command $Command -ErrorAction Stop
        Write-ColorOutput "✓ $Name is available" "Green"
        return $true
    } catch {
        Write-ColorOutput "✗ $Name is missing" "Red"
        Write-ColorOutput "  Install hint: $InstallHint" "Yellow"
        return $false
    }
}

function Test-PythonModule {
    param([string]$Module, [string]$InstallHint = "pip install $Module")
    
    try {
        $result = & python -c "import $Module; print('OK')" 2>&1
        if ($result -eq "OK") {
            Write-ColorOutput "✓ Python module '$Module' is available" "Green"
            return $true
        } else {
            Write-ColorOutput "✗ Python module '$Module' is missing" "Red"
            Write-ColorOutput "  Install hint: $InstallHint" "Yellow"
            return $false
        }
    } catch {
        Write-ColorOutput "✗ Python module '$Module' is missing" "Red"
        Write-ColorOutput "  Install hint: $InstallHint" "Yellow"
        return $false
    }
}

# Main execution starts here
Write-Header "Local Writing Assistant - Startup"

# Change to project directory
Set-Location $ProjectRoot
Write-ColorOutput "Project directory: $ProjectRoot" "Cyan"

# Create necessary directories
$DirsToCreate = @(".logs", ".run")
foreach ($dir in $DirsToCreate) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Verbose "Created directory: $dir"
    }
}

# Check system dependencies
Write-Section "Checking System Dependencies"

$missingDeps = @()

# Check Python 3.11+
if (Test-Dependency "python" "Python 3.11+" "winget install -e --id Python.Python.3.11") {
    try {
        $pythonVersion = & python --version 2>&1
        Write-ColorOutput "  Version: $pythonVersion" "Blue"
        
        # Check if it's Python 3.8+
        if ($pythonVersion -match "Python (\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 8)) {
                Write-ColorOutput "  Warning: Python $major.$minor detected. Python 3.8+ recommended." "Yellow"
            }
        }
    } catch {
        Write-ColorOutput "  Could not determine Python version" "Yellow"
    }
} else {
    $missingDeps += "Python"
}

# Check Java (for LanguageTool)
if (Test-Dependency "java" "Java JDK 17+" "winget install -e --id EclipseAdoptium.Temurin.17.JDK") {
    try {
        $javaVersion = & java -version 2>&1 | Select-Object -First 1
        Write-ColorOutput "  Version: $javaVersion" "Blue"
    } catch {
        Write-ColorOutput "  Could not determine Java version" "Yellow"
    }
} else {
    $missingDeps += "Java"
}

# Check FFmpeg (for audio processing)
if (Test-Dependency "ffmpeg" "FFmpeg" "winget install -e --id Gyan.FFmpeg") {
    try {
        $ffmpegVersion = & ffmpeg -version 2>&1 | Select-Object -First 1
        Write-ColorOutput "  Version: $($ffmpegVersion -replace 'ffmpeg version ', '')" "Blue"
    } catch {
        Write-ColorOutput "  Could not determine FFmpeg version" "Yellow"
    }
} else {
    $missingDeps += "FFmpeg"
}

# Handle missing dependencies
if ($missingDeps.Count -gt 0 -and !$Force) {
    Write-ColorOutput "`nMissing required dependencies: $($missingDeps -join ', ')" "Red"
    Write-ColorOutput "Options:" "Yellow"
    Write-ColorOutput "1. Run SetupEnv.ps1 to install all dependencies automatically" "Yellow"
    Write-ColorOutput "2. Install manually using the hints above" "Yellow"
    Write-ColorOutput "3. Use -Force to continue anyway (some features may not work)" "Yellow"
    
    $choice = Read-Host "`nWould you like to run SetupEnv.ps1 now? (y/N)"
    if ($choice -eq 'y' -or $choice -eq 'Y') {
        $setupScript = Join-Path $ScriptDir "SetupEnv.ps1"
        if (Test-Path $setupScript) {
            Write-ColorOutput "Running SetupEnv.ps1..." "Cyan"
            & powershell -ExecutionPolicy Bypass -File $setupScript
            if ($LASTEXITCODE -ne 0) {
                Write-ColorOutput "Setup failed. Please install dependencies manually." "Red"
                exit 1
            }
        } else {
            Write-ColorOutput "SetupEnv.ps1 not found at $setupScript" "Red"
            exit 1
        }
    } else {
        Write-ColorOutput "Please install the missing dependencies and try again." "Yellow"
        exit 1
    }
}

# Check and create Python virtual environment
Write-Section "Setting up Python Environment"

$venvPath = ".venv"
if (!(Test-Path $venvPath)) {
    Write-ColorOutput "Creating Python virtual environment..." "Cyan"
    try {
        & python -m venv $venvPath
        if ($LASTEXITCODE -ne 0) {
            throw "venv creation failed"
        }
        Write-ColorOutput "✓ Virtual environment created" "Green"
    } catch {
        Write-ColorOutput "✗ Failed to create virtual environment" "Red"
        Write-ColorOutput "Error: $($_.Exception.Message)" "Red"
        exit 1
    }
} else {
    Write-ColorOutput "✓ Virtual environment already exists" "Green"
}

# Activate virtual environment
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Write-ColorOutput "Activating virtual environment..." "Cyan"
    try {
        & $activateScript
        Write-ColorOutput "✓ Virtual environment activated" "Green"
    } catch {
        Write-ColorOutput "✗ Failed to activate virtual environment" "Red"
        exit 1
    }
} else {
    Write-ColorOutput "✗ Virtual environment activation script not found" "Red"
    exit 1
}

# Install/update Python dependencies
Write-Section "Installing Python Dependencies"

$requirementsFile = "server\requirements.txt"
if (Test-Path $requirementsFile) {
    Write-ColorOutput "Installing Python packages..." "Cyan"
    try {
        & python -m pip install -U pip wheel
        & python -m pip install -r $requirementsFile
        if ($LASTEXITCODE -ne 0) {
            throw "pip install failed"
        }
        Write-ColorOutput "✓ Python dependencies installed" "Green"
    } catch {
        Write-ColorOutput "✗ Failed to install Python dependencies" "Red"
        Write-ColorOutput "Error: $($_.Exception.Message)" "Red"
        exit 1
    }
} else {
    Write-ColorOutput "✗ Requirements file not found: $requirementsFile" "Red"
    exit 1
}

# Check/create .env file
Write-Section "Environment Configuration"

$envFile = ".env"
$envExampleFile = ".env.example"

if (!(Test-Path $envFile)) {
    if (Test-Path $envExampleFile) {
        Write-ColorOutput "Creating .env file from template..." "Cyan"
        Copy-Item $envExampleFile $envFile
        
        # Generate a secure API token
        $token = -join ((1..32) | ForEach-Object {Get-Random -InputObject ([char[]]"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")})
        
        # Replace placeholder token
        $envContent = Get-Content $envFile -Raw
        $envContent = $envContent -replace "your-secure-random-token-here", $token
        Set-Content $envFile $envContent
        
        Write-ColorOutput "✓ .env file created with generated API token" "Green"
    } else {
        Write-ColorOutput "✗ .env.example file not found" "Red"
        exit 1
    }
} else {
    Write-ColorOutput "✓ .env file already exists" "Green"
}

# Download models if needed
Write-Section "Checking AI Models"

$modelsDir = "server\models"
$downloadScript = "server\scripts\download_models.py"

if (!(Test-Path $modelsDir) -or (Get-ChildItem $modelsDir -Recurse | Measure-Object).Count -eq 0) {
    if (Test-Path $downloadScript) {
        Write-ColorOutput "Downloading AI models (this may take a few minutes)..." "Cyan"
        try {
            & python $downloadScript
            if ($LASTEXITCODE -ne 0) {
                throw "Model download failed"
            }
            Write-ColorOutput "✓ AI models downloaded" "Green"
        } catch {
            Write-ColorOutput "⚠ Model download failed, but continuing..." "Yellow"
            Write-ColorOutput "Some features may not work until models are downloaded." "Yellow"
        }
    } else {
        Write-ColorOutput "⚠ Model download script not found" "Yellow"
    }
} else {
    Write-ColorOutput "✓ AI models appear to be present" "Green"
}

# Check if ports are in use
Write-Section "Checking Network Ports"

$serverPort = 8000
$ltPort = 8010

if (Test-Port $serverPort) {
    Write-ColorOutput "Port $serverPort is in use" "Yellow"
    if (!$Force) {
        $choice = Read-Host "Stop existing service on port $serverPort? (Y/n)"
        if ($choice -ne 'n' -and $choice -ne 'N') {
            Stop-ProcessByPort $serverPort
        }
    } else {
        Stop-ProcessByPort $serverPort
    }
}

if (Test-Port $ltPort) {
    Write-ColorOutput "Port $ltPort is in use" "Yellow"
    Stop-ProcessByPort $ltPort
}

# Start the services
Write-Section "Starting Services"

# Start FastAPI server
Write-ColorOutput "Starting Local Writing Assistant server..." "Cyan"

try {
    $logFile = ".logs\uvicorn.log"
    $pidFile = ".run\uvicorn.pid"
    
    # Start uvicorn in background
    $process = Start-Process -FilePath "python" -ArgumentList @("-m", "uvicorn", "server.main:app", "--host", "127.0.0.1", "--port", "$serverPort", "--reload") -NoNewWindow -PassThru -RedirectStandardOutput $logFile -RedirectStandardError $logFile
    
    # Save PID
    $process.Id | Out-File $pidFile -Encoding ASCII
    
    Write-ColorOutput "✓ Server started (PID: $($process.Id))" "Green"
    
    # Wait a moment for server to start
    Start-Sleep -Seconds 3
    
    # Test server health
    for ($i = 1; $i -le 10; $i++) {
        if (Test-Port $serverPort) {
            try {
                $response = Invoke-RestMethod -Uri "http://127.0.0.1:$serverPort/health" -Method Get -TimeoutSec 5
                if ($response.ok) {
                    Write-ColorOutput "✓ Server is healthy and responding" "Green"
                    break
                }
            } catch {
                Write-Verbose "Health check attempt $i failed: $($_.Exception.Message)"
            }
        }
        
        if ($i -eq 10) {
            Write-ColorOutput "⚠ Server started but health check failed" "Yellow"
            Write-ColorOutput "Check logs at: $logFile" "Yellow"
        } else {
            Start-Sleep -Seconds 2
        }
    }
    
} catch {
    Write-ColorOutput "✗ Failed to start server" "Red"
    Write-ColorOutput "Error: $($_.Exception.Message)" "Red"
    exit 1
}

# Final status and next steps
Write-Header "Local Writing Assistant Started Successfully!"

Write-ColorOutput "🚀 Services Status:" "Green"
Write-ColorOutput "   Server: http://127.0.0.1:$serverPort" "White"
Write-ColorOutput "   API Documentation: http://127.0.0.1:$serverPort/docs" "White"
Write-ColorOutput "   Health Check: http://127.0.0.1:$serverPort/health" "White"

Write-ColorOutput "`n📁 Important Files:" "Blue"
Write-ColorOutput "   Logs: .logs\uvicorn.log" "White"
Write-ColorOutput "   PID: .run\uvicorn.pid" "White"
Write-ColorOutput "   Config: .env" "White"

Write-ColorOutput "`n🔧 Next Steps:" "Magenta"
Write-ColorOutput "   1. Load the Chrome extension from /extension" "White"
Write-ColorOutput "   2. In Chrome: Extensions > Developer Mode > Load unpacked" "White"
Write-ColorOutput "   3. Select the 'extension' folder" "White"
Write-ColorOutput "   4. Configure the extension with your API token (found in .env)" "White"

Write-ColorOutput "`n⚡ Quick Commands:" "Yellow"
Write-ColorOutput "   Stop server: .\scripts\windows\StopLocalAssistant.ps1" "White"
Write-ColorOutput "   View logs: Get-Content .logs\uvicorn.log -Tail 20 -Wait" "White"

# Open browser unless requested not to
if (!$SkipBrowser) {
    Write-ColorOutput "`nOpening API documentation in browser..." "Cyan"
    Start-Process "http://127.0.0.1:$serverPort/docs"
}

Write-ColorOutput "`n✅ Local Writing Assistant is ready!" "Green"
