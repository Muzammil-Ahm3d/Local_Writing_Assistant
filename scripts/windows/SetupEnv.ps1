# SetupEnv.ps1
# Local Writing Assistant - Environment Setup Script
# Automatically installs all required dependencies using winget

param(
    [switch]$Verbose,
    [switch]$SkipPython,
    [switch]$SkipJava,
    [switch]$SkipFFmpeg,
    [switch]$SkipVCRedist,
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

function Write-Section {
    param([string]$Title)
    Write-ColorOutput "`n$('-'*40)" "Blue"
    Write-ColorOutput "$Title" "Blue"
    Write-ColorOutput "$('-'*40)" "Blue"
}

function Test-WingetAvailable {
    try {
        $null = Get-Command winget -ErrorAction Stop
        # Test if winget actually works
        $result = winget --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✓ winget is available: $result" "Green"
            return $true
        } else {
            Write-ColorOutput "✗ winget command failed" "Red"
            return $false
        }
    } catch {
        Write-ColorOutput "✗ winget is not available" "Red"
        return $false
    }
}

function Install-WithWinget {
    param([string]$PackageId, [string]$Name, [string]$SkipCheck = $null)
    
    if ($SkipCheck -and (Get-Variable $SkipCheck -ErrorAction SilentlyContinue).Value) {
        Write-ColorOutput "⏭ Skipping $Name installation (user requested)" "Yellow"
        return $true
    }
    
    Write-ColorOutput "Installing $Name..." "Cyan"
    
    try {
        # Try to install with winget
        $result = winget install -e --id $PackageId --silent --accept-package-agreements --accept-source-agreements 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✓ $Name installed successfully" "Green"
            return $true
        } elseif ($result -match "No available upgrade found" -or $result -match "already installed") {
            Write-ColorOutput "✓ $Name is already installed" "Green"
            return $true
        } else {
            Write-ColorOutput "✗ Failed to install $Name" "Red"
            Write-ColorOutput "  winget output: $result" "Red"
            return $false
        }
    } catch {
        Write-ColorOutput "✗ Failed to install ${Name}: $($_.Exception.Message)" "Red"
        return $false
    }
}

function Test-Dependency {
    param([string]$Command, [string]$Name)
    
    try {
        $null = Get-Command $Command -ErrorAction Stop
        Write-ColorOutput "✓ $Name is available" "Green"
        return $true
    } catch {
        Write-ColorOutput "✗ $Name is not available" "Red"
        return $false
    }
}

function Install-PythonPackages {
    Write-ColorOutput "Setting up Python environment..." "Cyan"
    
    # Change to project directory
    Set-Location $ProjectRoot
    
    # Create virtual environment if it doesn't exist
    if (!(Test-Path ".venv")) {
        Write-ColorOutput "Creating Python virtual environment..." "Blue"
        try {
            & python -m venv .venv
            if ($LASTEXITCODE -ne 0) {
                throw "venv creation failed"
            }
            Write-ColorOutput "✓ Virtual environment created" "Green"
        } catch {
            Write-ColorOutput "✗ Failed to create virtual environment: $($_.Exception.Message)" "Red"
            return $false
        }
    } else {
        Write-ColorOutput "✓ Virtual environment already exists" "Green"
    }
    
    # Activate virtual environment
    $activateScript = ".venv\Scripts\Activate.ps1"
    if (Test-Path $activateScript) {
        Write-ColorOutput "Activating virtual environment..." "Blue"
        try {
            & $activateScript
            Write-ColorOutput "✓ Virtual environment activated" "Green"
        } catch {
            Write-ColorOutput "✗ Failed to activate virtual environment" "Red"
            return $false
        }
    } else {
        Write-ColorOutput "✗ Virtual environment activation script not found" "Red"
        return $false
    }
    
    # Install Python packages
    $requirementsFile = "server\requirements.txt"
    if (Test-Path $requirementsFile) {
        Write-ColorOutput "Installing Python packages..." "Blue"
        try {
            & python -m pip install -U pip wheel
            & python -m pip install -r $requirementsFile
            if ($LASTEXITCODE -ne 0) {
                throw "pip install failed"
            }
            Write-ColorOutput "✓ Python packages installed" "Green"
            return $true
        } catch {
            Write-ColorOutput "✗ Failed to install Python packages: $($_.Exception.Message)" "Red"
            return $false
        }
    } else {
        Write-ColorOutput "✗ Requirements file not found: $requirementsFile" "Red"
        return $false
    }
}

function Download-AIModels {
    Write-ColorOutput "Downloading AI models..." "Cyan"
    
    $downloadScript = "server\scripts\download_models.py"
    if (Test-Path $downloadScript) {
        try {
            & python $downloadScript
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "✓ AI models downloaded successfully" "Green"
                return $true
            } else {
                Write-ColorOutput "⚠ Model download completed with warnings" "Yellow"
                return $true  # Continue anyway
            }
        } catch {
            Write-ColorOutput "⚠ Model download failed, but continuing: $($_.Exception.Message)" "Yellow"
            return $true  # Continue anyway
        }
    } else {
        Write-ColorOutput "⚠ Model download script not found" "Yellow"
        return $true  # Continue anyway
    }
}

# Main execution starts here
Write-Header "Local Writing Assistant - Environment Setup"

Write-ColorOutput "This script will install all required dependencies for the Local Writing Assistant." "White"
Write-ColorOutput "Dependencies to install:" "Yellow"
Write-ColorOutput "  - Python 3.11" "White"
Write-ColorOutput "  - Java JDK 17 (Eclipse Temurin)" "White" 
Write-ColorOutput "  - Git" "White"
Write-ColorOutput "  - FFmpeg" "White"
Write-ColorOutput "  - Microsoft Visual C++ Redistributable" "White"
Write-ColorOutput "  - Python packages (via pip)" "White"
Write-ColorOutput "  - AI models (Flan-T5-small, Whisper)" "White"

if (!$Force) {
    $continue = Read-Host "`nDo you want to continue? (Y/n)"
    if ($continue -eq 'n' -or $continue -eq 'N') {
        Write-ColorOutput "Setup cancelled by user." "Yellow"
        exit 0
    }
}

# Check if winget is available
Write-Section "Checking Package Manager"

if (!(Test-WingetAvailable)) {
    Write-ColorOutput "`nwinget is required but not available." "Red"
    Write-ColorOutput "Please install winget (Windows Package Manager) first:" "Yellow"
    Write-ColorOutput "1. Install from Microsoft Store: 'App Installer'" "White"
    Write-ColorOutput "2. Or download from: https://github.com/microsoft/winget-cli/releases" "White"
    Write-ColorOutput "3. Or run: Add-AppxPackage -RegisterByFamilyName -MainPackage Microsoft.DesktopAppInstaller_8wekyb3d8bbwe" "White"
    exit 1
}

# Install dependencies
Write-Section "Installing System Dependencies"

$installSuccess = $true

# Install Python 3.11
if (!(Install-WithWinget "Python.Python.3.11" "Python 3.11" "SkipPython")) {
    $installSuccess = $false
}

# Install Java JDK 17
if (!(Install-WithWinget "EclipseAdoptium.Temurin.17.JDK" "Java JDK 17" "SkipJava")) {
    $installSuccess = $false
}

# Install Git
if (!(Install-WithWinget "Git.Git" "Git" $null)) {
    Write-ColorOutput "⚠ Git installation failed, but continuing..." "Yellow"
}

# Install FFmpeg
if (!(Install-WithWinget "Gyan.FFmpeg" "FFmpeg" "SkipFFmpeg")) {
    $installSuccess = $false
}

# Install Visual C++ Redistributable
if (!(Install-WithWinget "Microsoft.VCRedist.2015+.x64" "Visual C++ Redistributable" "SkipVCRedist")) {
    Write-ColorOutput "⚠ Visual C++ Redistributable installation failed, but continuing..." "Yellow"
}

# Check if core dependencies are now available (they might need a PATH refresh)
Write-Section "Verifying Installation"

Write-ColorOutput "Refreshing environment variables..." "Blue"
$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","User")

$coreInstalled = $true

if (!(Test-Dependency "python" "Python")) {
    $coreInstalled = $false
    Write-ColorOutput "Try running: refreshenv" "Yellow"
}

if (!(Test-Dependency "java" "Java")) {
    $coreInstalled = $false
    Write-ColorOutput "Try running: refreshenv" "Yellow"
}

if (!(Test-Dependency "ffmpeg" "FFmpeg")) {
    $coreInstalled = $false
    Write-ColorOutput "Try running: refreshenv" "Yellow"
}

if (!$coreInstalled) {
    Write-ColorOutput "`n⚠ Some core dependencies are not available in PATH." "Yellow"
    Write-ColorOutput "This often happens after fresh installations." "Yellow"
    Write-ColorOutput "Solutions:" "Yellow"
    Write-ColorOutput "1. Restart your terminal/PowerShell session" "White"
    Write-ColorOutput "2. Restart your computer" "White"
    Write-ColorOutput "3. Run: refreshenv (if you have Chocolatey)" "White"
    Write-ColorOutput "4. Re-run this script after restarting" "White"
    
    if (!$Force) {
        $continue = Read-Host "`nContinue with Python setup anyway? (y/N)"
        if ($continue -ne 'y' -and $continue -ne 'Y') {
            Write-ColorOutput "Please restart your terminal and re-run this script." "Yellow"
            exit 1
        }
    }
}

# Install Python packages
Write-Section "Setting up Python Environment"

if (!(Install-PythonPackages)) {
    $installSuccess = $false
    Write-ColorOutput "Python package installation failed." "Red"
} 

# Download AI models
Write-Section "Downloading AI Models"

if (!(Download-AIModels)) {
    Write-ColorOutput "⚠ AI model download had issues, but continuing..." "Yellow"
}

# Final summary
Write-Header "Setup Complete"

if ($installSuccess -and $coreInstalled) {
    Write-ColorOutput "✅ Environment setup completed successfully!" "Green"
    
    Write-ColorOutput "`n🎉 What's installed:" "Blue"
    Write-ColorOutput "   ✓ Python 3.11 with virtual environment" "White"
    Write-ColorOutput "   ✓ Java JDK 17 (for LanguageTool)" "White"
    Write-ColorOutput "   ✓ FFmpeg (for audio processing)" "White"
    Write-ColorOutput "   ✓ Python packages (FastAPI, AI models, etc.)" "White"
    Write-ColorOutput "   ✓ AI models (Flan-T5-small, Whisper)" "White"
    
    Write-ColorOutput "`n🚀 Next steps:" "Magenta"
    Write-ColorOutput "   1. Run: .\scripts\windows\StartLocalAssistant.bat" "White"
    Write-ColorOutput "   2. Load Chrome extension from /extension folder" "White"
    Write-ColorOutput "   3. Start writing with AI assistance!" "White"
    
    Write-ColorOutput "`n📚 Quick start:" "Yellow"
    $startScript = Join-Path $ScriptDir "StartLocalAssistant.bat"
    Write-ColorOutput "   Double-click: $startScript" "White"
    
} else {
    Write-ColorOutput "⚠ Environment setup completed with some issues." "Yellow"
    
    if (!$coreInstalled) {
        Write-ColorOutput "`n🔧 To fix PATH issues:" "Red"
        Write-ColorOutput "   1. Restart your terminal/PowerShell" "White"
        Write-ColorOutput "   2. Re-run this script" "White"
        Write-ColorOutput "   3. Or restart your computer" "White"
    }
    
    if (!$installSuccess) {
        Write-ColorOutput "`n🔧 To fix installation issues:" "Red"
        Write-ColorOutput "   1. Check your internet connection" "White"
        Write-ColorOutput "   2. Run as Administrator if needed" "White"
        Write-ColorOutput "   3. Install missing components manually" "White"
    }
}

Write-ColorOutput "`n💡 Troubleshooting:" "Cyan"
Write-ColorOutput "   - Logs: Check winget logs in Event Viewer" "White"
Write-ColorOutput "   - Manual install: Use the winget commands shown above" "White"
Write-ColorOutput "   - Help: Check README.md for detailed instructions" "White"

if ($installSuccess -and $coreInstalled) {
    exit 0
} else {
    exit 1
}
