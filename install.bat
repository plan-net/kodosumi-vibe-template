@echo off
echo Setting up kodosumi-vibe-template environment...

REM Check Python version
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

for /f "tokens=2" %%I in ('python --version 2^>^&1') do set PYTHON_VERSION=%%I
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set PYTHON_MAJOR=%%a
    set PYTHON_MINOR=%%b
)

if %PYTHON_MAJOR% LSS 3 (
    echo Error: Python 3.8 or higher is required (found %PYTHON_VERSION%)
    exit /b 1
)

if %PYTHON_MAJOR% EQU 3 (
    if %PYTHON_MINOR% LSS 8 (
        echo Error: Python 3.8 or higher is required (found %PYTHON_VERSION%)
        exit /b 1
    )
)

echo Python %PYTHON_VERSION% detected

REM Create and activate virtual environment
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install the project in development mode
echo Installing project in development mode...
pip install -e .

REM Install development dependencies
echo Installing development dependencies...
pip install -e ".[dev]"

REM Install Kodosumi from GitHub
echo Installing Kodosumi from GitHub (dev branch)...
pip install git+https://github.com/masumi-network/kodosumi.git@dev

REM Copy .env.example to .env if it doesn't exist
if not exist .env (
    echo Creating .env file from .env.example...
    copy .env.example .env
    echo Please edit .env file with your API keys
)

echo Installation complete!
echo To activate the environment, run:
echo venv\Scripts\activate.bat 