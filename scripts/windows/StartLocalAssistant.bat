@echo off
REM StartLocalAssistant.bat
REM Local Writing Assistant - Direct Batch Implementation
REM Single-click start with health checks

setlocal EnableDelayedExpansion

REM Colors (limited in batch)
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "CYAN=[96m"
set "WHITE=[97m"
set "RESET=[0m"

echo %CYAN%============================================================%RESET%
echo %CYAN%Local Writing Assistant - Startup%RESET%
echo %CYAN%============================================================%RESET%

REM Get paths
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\..\" 
echo %GREEN%Project directory: %PROJECT_ROOT%%RESET%

REM Change to project directory
cd /d "%PROJECT_ROOT%"

REM Create directories
if not exist ".logs" mkdir ".logs"
if not exist ".run" mkdir ".run"

echo.
echo %BLUE%--------------------------------------------%RESET%
echo %BLUE%Checking Dependencies%RESET%
echo %BLUE%--------------------------------------------%RESET%

REM Check Python
python --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo %GREEN%✓ Python is available%RESET%
    for /f "tokens=*" %%a in ('python --version 2^>^&1') do echo   Version: %%a
) else (
    echo %RED%✗ Python is missing%RESET%
    echo %YELLOW%  Install: winget install -e --id Python.Python.3.11%RESET%
    pause
    exit /b 1
)

REM Check Java
java -version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo %GREEN%✓ Java is available%RESET%
) else (
    echo %RED%✗ Java is missing%RESET%
    echo %YELLOW%  Install: winget install -e --id EclipseAdoptium.Temurin.17.JDK%RESET%
    pause
    exit /b 1
)

REM Check FFmpeg
ffmpeg -version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo %GREEN%✓ FFmpeg is available%RESET%
) else (
    echo %RED%✗ FFmpeg is missing%RESET%
    echo %YELLOW%  Install: winget install -e --id Gyan.FFmpeg%RESET%
    pause
    exit /b 1
)

echo.
echo %BLUE%--------------------------------------------%RESET%
echo %BLUE%Setting up Python Environment%RESET%
echo %BLUE%--------------------------------------------%RESET%

REM Create virtual environment
if not exist ".venv" (
    echo %YELLOW%Creating Python virtual environment...%RESET%
    python -m venv .venv
    if !ERRORLEVEL! neq 0 (
        echo %RED%✗ Failed to create virtual environment%RESET%
        pause
        exit /b 1
    )
    echo %GREEN%✓ Virtual environment created%RESET%
) else (
    echo %GREEN%✓ Virtual environment already exists%RESET%
)

REM Activate virtual environment and install packages
if exist ".venv\Scripts\activate.bat" (
    echo %YELLOW%Activating virtual environment...%RESET%
    call .venv\Scripts\activate.bat
    echo %GREEN%✓ Virtual environment activated%RESET%
) else (
    echo %RED%✗ Virtual environment activation script not found%RESET%
    pause
    exit /b 1
)

REM Install Python packages
if exist "server\requirements.txt" (
    echo %YELLOW%Installing Python packages...%RESET%
    python -m pip install -U pip wheel
    python -m pip install -r server\requirements.txt
    if !ERRORLEVEL! equ 0 (
        echo %GREEN%✓ Python dependencies installed%RESET%
    ) else (
        echo %RED%✗ Failed to install Python dependencies%RESET%
        pause
        exit /b 1
    )
) else (
    echo %RED%✗ Requirements file not found%RESET%
    pause
    exit /b 1
)

echo.
echo %BLUE%--------------------------------------------%RESET%
echo %BLUE%Environment Configuration%RESET%
echo %BLUE%--------------------------------------------%RESET%

REM Create .env file
if not exist ".env" (
    if exist ".env.example" (
        echo %YELLOW%Creating .env file from template...%RESET%
        copy ".env.example" ".env" >nul
        
        REM Generate a simple random token
        set "TOKEN="
        for /L %%i in (1,1,32) do (
            set /a "rand=!RANDOM! %% 62"
            if !rand! lss 10 (
                set /a "char=48+!rand!"
            ) else if !rand! lss 36 (
                set /a "char=55+!rand!"
            ) else (
                set /a "char=61+!rand!"
            )
            for /f "tokens=* usebackq" %%a in (`powershell -c "[char]!char!"`) do set "TOKEN=!TOKEN!%%a"
        )
        
        REM Replace token in .env (simple approach)
        powershell -c "(Get-Content '.env') -replace 'your-secure-random-token-here', '%TOKEN%' | Set-Content '.env'"
        
        echo %GREEN%✓ .env file created with API token%RESET%
    ) else (
        echo %RED%✗ .env.example not found%RESET%
        pause
        exit /b 1
    )
) else (
    echo %GREEN%✓ .env file already exists%RESET%
)

echo.
echo %BLUE%--------------------------------------------%RESET%
echo %BLUE%Downloading AI Models%RESET%
echo %BLUE%--------------------------------------------%RESET%

if exist "server\scripts\download_models.py" (
    echo %YELLOW%Downloading models (this may take a few minutes)...%RESET%
    python server\scripts\download_models.py
    if !ERRORLEVEL! equ 0 (
        echo %GREEN%✓ AI models downloaded%RESET%
    ) else (
        echo %YELLOW%⚠ Model download had issues, continuing...%RESET%
    )
) else (
    echo %YELLOW%⚠ Model download script not found%RESET%
)

echo.
echo %BLUE%--------------------------------------------%RESET%
echo %BLUE%Starting Server%RESET%
echo %BLUE%--------------------------------------------%RESET%

echo %YELLOW%Starting Local Writing Assistant server...%RESET%

REM Start server in background
start /b python -m uvicorn server.main:app --host 127.0.0.1 --port 8000 --reload > .logs\uvicorn.log 2>&1

REM Get the PID (approximate)
for /f "tokens=2" %%a in ('tasklist /fi "imagename eq python.exe" /fo csv ^| find "python.exe"') do (
    echo %%a > .run\uvicorn.pid
    goto :found_pid
)
:found_pid

echo %GREEN%✓ Server starting...%RESET%

REM Wait and test
echo %YELLOW%Waiting for server to start...%RESET%
timeout /t 8 /nobreak >nul

REM Test health
curl -s http://127.0.0.1:8000/health >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo %GREEN%✓ Server is healthy and responding%RESET%
) else (
    echo %YELLOW%⚠ Server started but health check failed%RESET%
    echo Check logs at: .logs\uvicorn.log
)

echo.
echo %CYAN%============================================================%RESET%
echo %CYAN%Local Writing Assistant Started Successfully!%RESET%
echo %CYAN%============================================================%RESET%

echo.
echo %GREEN%🚀 Services:%RESET%
echo    Server: http://127.0.0.1:8000
echo    API Docs: http://127.0.0.1:8000/docs

echo.
echo %BLUE%📁 Files:%RESET%
echo    Logs: .logs\uvicorn.log
echo    Config: .env

echo.
echo %CYAN%🔧 Next Steps:%RESET%
echo    1. Load Chrome extension from /extension
echo    2. Chrome: Extensions → Developer Mode → Load unpacked
echo    3. Select the 'extension' folder
echo    4. Configure with API token (in .env file)

echo.
echo %YELLOW%⚡ Commands:%RESET%
echo    Stop: .\scripts\windows\StopLocalAssistant.ps1

REM Open browser
echo.
echo %CYAN%Opening API documentation...%RESET%
start http://127.0.0.1:8000/docs

echo.
echo %GREEN%✅ Local Writing Assistant is ready!%RESET%
echo.
echo Press any key to close this window...
pause >nul
