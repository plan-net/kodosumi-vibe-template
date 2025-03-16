@echo off
echo Setting up kodosumi-vibe-template environment...

REM Check Python version
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

for /f "tokens=2" %%I in ('python --version 2^>^&1') do set PYTHON_VERSION=%%I
for /f "tokens=1,2,3 delims=." %%a in ("%PYTHON_VERSION%") do (
    set PYTHON_MAJOR=%%a
    set PYTHON_MINOR=%%b
    set PYTHON_PATCH=%%c
)

if %PYTHON_MAJOR% NEQ 3 (
    echo Error: Python 3.12.2 is required (found %PYTHON_VERSION%)
    exit /b 1
)

if %PYTHON_MINOR% NEQ 12 (
    echo Error: Python 3.12.2 is required (found %PYTHON_VERSION%)
    exit /b 1
)

if %PYTHON_PATCH% NEQ 2 (
    echo Error: Python 3.12.2 is required (found %PYTHON_VERSION%)
    exit /b 1
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

REM Install dependencies with specific versions
echo Installing dependencies with specific versions...
pip install "crewai==0.105.0" "ray>=2.6.0" "langchain>=0.0.267" "langchain-openai>=0.0.2" "langchain-community>=0.0.10"

REM Install Kodosumi from GitHub
echo.
echo NOTE: Kodosumi is not available on PyPI and must be installed from GitHub
echo Installing Kodosumi from GitHub (dev branch)...
pip install git+https://github.com/masumi-network/kodosumi.git@dev

REM Copy .env.example to .env if it doesn't exist
if not exist .env (
    echo Creating .env file from .env.example...
    copy .env.example .env
    echo Please edit .env file with your API keys
)

echo.
echo Installation complete!
echo To activate the environment, run:
echo venv\Scripts\activate.bat 