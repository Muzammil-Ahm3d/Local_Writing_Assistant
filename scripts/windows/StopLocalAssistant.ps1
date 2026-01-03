# StopLocalAssistant.ps1
# Local Writing Assistant - Stop Script
# Gracefully shutdown all services

param(
    [switch]$Verbose,
    [switch]$Force
)

# Set error handling
$ErrorActionPreference = "Continue"
$VerbosePreference = if ($Verbose) { "Continue" } else { "SilentlyContinue" }

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

function Stop-ServiceByPid {
    param([string]$PidFile, [string]$ServiceName)
    
    if (Test-Path $PidFile) {
        try {
            $pid = Get-Content $PidFile -ErrorAction Stop
            $pid = $pid.Trim()
            
            if ($pid -match '^\d+$') {
                $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
                if ($process) {
                    Write-ColorOutput "Stopping $ServiceName (PID: $pid)..." "Yellow"
                    Stop-Process -Id $pid -Force -ErrorAction Stop
                    
                    # Wait for process to stop
                    $timeout = 10
                    while ($timeout -gt 0 -and (Get-Process -Id $pid -ErrorAction SilentlyContinue)) {
                        Start-Sleep -Seconds 1
                        $timeout--
                    }
                    
                    if (Get-Process -Id $pid -ErrorAction SilentlyContinue) {
                        Write-ColorOutput "⚠ $ServiceName may still be running" "Yellow"
                        return $false
                    } else {
                        Write-ColorOutput "✓ $ServiceName stopped successfully" "Green"
                        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
                        return $true
                    }
                } else {
                    Write-ColorOutput "✓ $ServiceName was not running (stale PID file)" "Green"
                    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
                    return $true
                }
            } else {
                Write-ColorOutput "✗ Invalid PID in $PidFile: $pid" "Red"
                Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
                return $false
            }
        } catch {
            Write-ColorOutput "✗ Failed to stop $ServiceName: $($_.Exception.Message)" "Red"
            Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
            return $false
        }
    } else {
        Write-ColorOutput "✓ $ServiceName was not running (no PID file)" "Green"
        return $true
    }
}

function Stop-ProcessByPort {
    param([int]$Port, [string]$ServiceName)
    
    try {
        $connections = netstat -ano | findstr ":$Port "
        $stopped = $false
        
        foreach ($line in $connections) {
            if ($line -match '\s+(\d+)$') {
                $pid = $matches[1]
                $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
                if ($process) {
                    Write-ColorOutput "Stopping $ServiceName on port $Port (PID: $pid)..." "Yellow"
                    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                    $stopped = $true
                }
            }
        }
        
        if ($stopped) {
            Start-Sleep -Seconds 2
            Write-ColorOutput "✓ Processes on port $Port stopped" "Green"
        } else {
            Write-ColorOutput "✓ No processes found on port $Port" "Green"
        }
        
        return $true
    } catch {
        Write-ColorOutput "✗ Failed to stop processes on port $Port: $($_.Exception.Message)" "Red"
        return $false
    }
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

# Main execution starts here
Write-Header "Local Writing Assistant - Shutdown"

# Change to project directory
Set-Location $ProjectRoot
Write-ColorOutput "Project directory: $ProjectRoot" "Cyan"

# Stop services by PID files
Write-ColorOutput "`nStopping services..." "Blue"

$runDir = ".run"
$success = $true

# Stop FastAPI server
$uvicornPid = Join-Path $runDir "uvicorn.pid"
if (!(Stop-ServiceByPid $uvicornPid "FastAPI Server")) {
    $success = $false
}

# Stop LanguageTool server if it has a PID file
$ltPid = Join-Path $runDir "languagetool.pid"
if (Test-Path $ltPid) {
    if (!(Stop-ServiceByPid $ltPid "LanguageTool Server")) {
        $success = $false
    }
}

# Fallback: Stop processes by port
Write-ColorOutput "`nChecking ports..." "Blue"

$serverPort = 8000
$ltPort = 8010

if (Test-Port $serverPort) {
    Write-ColorOutput "Port $serverPort still in use, stopping processes..." "Yellow"
    if (!(Stop-ProcessByPort $serverPort "FastAPI Server")) {
        $success = $false
    }
}

if (Test-Port $ltPort) {
    Write-ColorOutput "Port $ltPort still in use, stopping processes..." "Yellow"
    if (!(Stop-ProcessByPort $ltPort "LanguageTool Server")) {
        $success = $false
    }
}

# Clean up stale PID files
Write-ColorOutput "`nCleaning up..." "Blue"

if (Test-Path $runDir) {
    $pidFiles = Get-ChildItem $runDir -Filter "*.pid" -ErrorAction SilentlyContinue
    if ($pidFiles) {
        foreach ($file in $pidFiles) {
            Write-Verbose "Removing stale PID file: $($file.Name)"
            Remove-Item $file.FullName -Force -ErrorAction SilentlyContinue
        }
        Write-ColorOutput "✓ Cleaned up PID files" "Green"
    }
}

# Final status check
Write-ColorOutput "`nFinal status check..." "Blue"

$stillRunning = @()

if (Test-Port $serverPort) {
    $stillRunning += "FastAPI Server (port $serverPort)"
}

if (Test-Port $ltPort) {
    $stillRunning += "LanguageTool Server (port $ltPort)"
}

# Summary
Write-Header "Shutdown Complete"

if ($stillRunning.Count -eq 0) {
    Write-ColorOutput "✅ All services stopped successfully" "Green"
    Write-ColorOutput "`n📊 Status:" "Blue"
    Write-ColorOutput "   FastAPI Server: ⭕ Stopped" "White"
    Write-ColorOutput "   LanguageTool Server: ⭕ Stopped" "White"
    Write-ColorOutput "   Port 8000: 🔓 Free" "White"
    Write-ColorOutput "   Port 8010: 🔓 Free" "White"
} else {
    Write-ColorOutput "⚠ Some services may still be running:" "Yellow"
    foreach ($service in $stillRunning) {
        Write-ColorOutput "   - $service" "Yellow"
    }
    
    if ($Force) {
        Write-ColorOutput "`nForce stopping remaining processes..." "Red"
        Stop-ProcessByPort $serverPort "Remaining processes"
        Stop-ProcessByPort $ltPort "Remaining processes"
    } else {
        Write-ColorOutput "`nUse -Force to forcefully stop remaining processes" "Yellow"
        $success = $false
    }
}

Write-ColorOutput "`n💡 Tips:" "Magenta"
Write-ColorOutput "   Start again: .\scripts\windows\StartLocalAssistant.ps1" "White"
Write-ColorOutput "   View logs: Get-Content .logs\uvicorn.log" "White"
Write-ColorOutput "   Clean restart: Remove-Item .logs\*, .run\* -Force" "White"

if ($success) {
    Write-ColorOutput "`n✅ Local Writing Assistant stopped cleanly" "Green"
    exit 0
} else {
    Write-ColorOutput "`n⚠ Some issues occurred during shutdown" "Yellow"
    exit 1
}
