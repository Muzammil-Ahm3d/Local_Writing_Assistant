@echo off
REM Simple server starter
echo ============================================================
echo Starting Local Writing Assistant Server
echo ============================================================

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Set Python path
set PYTHONPATH=%CD%;%PYTHONPATH%

echo Environment: Virtual environment activated
echo Python path: %PYTHONPATH%

echo.
echo Starting server at http://127.0.0.1:8000
echo API docs will be available at http://127.0.0.1:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the server
python -m uvicorn server.main:app --host 127.0.0.1 --port 8000 --reload

pause
