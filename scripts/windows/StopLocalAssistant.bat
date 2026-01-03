@echo off
REM StopLocalAssistant.bat
REM Local Writing Assistant - Stop (Batch Wrapper)
REM This wrapper allows running the PowerShell script without changing execution policy

setlocal

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"
set "PS_SCRIPT=%SCRIPT_DIR%StopLocalAssistant.ps1"

REM Check if PowerShell script exists
if not exist "%PS_SCRIPT%" (
    echo ERROR: PowerShell script not found at: %PS_SCRIPT%
    pause
    exit /b 1
)

REM Run PowerShell script with bypass execution policy
echo Stopping Local Writing Assistant...
powershell.exe -ExecutionPolicy Bypass -File "%PS_SCRIPT%" %*

REM Capture exit code
set "EXIT_CODE=%ERRORLEVEL%"

REM Always pause so user can see the result
echo.
if %EXIT_CODE% equ 0 (
    echo Local Writing Assistant stopped successfully.
) else (
    echo Script completed with warnings ^(exit code: %EXIT_CODE%^)
)
pause

exit /b %EXIT_CODE%
