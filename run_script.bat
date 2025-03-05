@echo off
cd /d "%~dp0"  REM Change to the script's directory

REM Set execution policy for PowerShell scripts
powershell -Command "Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force"

REM Check if 'python' or 'py' is available
where python >nul 2>nul
if %errorlevel%==0 (
    set PYTHON_CMD=python
) else (
    set PYTHON_CMD=py
)

REM Activate virtual environment or create if missing
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Creating one...
    %PYTHON_CMD% -m venv .venv
    call .venv\Scripts\activate.bat
)

REM Install dependencies
pip install -r requirement.txt

REM Navigate to backend folder
cd backend

REM Start Flask app in a new terminal window
start "Flask Server" cmd /k %PYTHON_CMD% app.py

REM Wait for the server to start by checking if it's accessible
echo Waiting for Flask server to start...
:CHECK
timeout /t 2 >nul
curl --silent --head http://127.0.0.1:5000/ | find "200 OK" >nul
if errorlevel 1 goto CHECK

REM Open browser after the server is up
start "" http://127.0.0.1:5000/