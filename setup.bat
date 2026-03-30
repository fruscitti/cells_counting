@echo off
setlocal EnableDelayedExpansion

echo =============================================
echo   Cell Counter - Setup
echo =============================================
echo.

REM --- Locate Python (existing install or just-installed) ---
set PYTHON_EXE=
set PYTHON_LOCAL=%LOCALAPPDATA%\Programs\Python\Python311\python.exe
set PYTHON_LOCAL312=%LOCALAPPDATA%\Programs\Python\Python312\python.exe

where python >nul 2>&1
if %errorlevel% == 0 (
    for /f "tokens=2 delims= " %%V in ('python --version 2^>^&1') do set PY_VER=%%V
    echo Found Python !PY_VER! on PATH.
    set PYTHON_EXE=python
    goto :create_venv
)

if exist "%PYTHON_LOCAL%" (
    echo Found Python 3.11 at %PYTHON_LOCAL%
    set PYTHON_EXE=%PYTHON_LOCAL%
    goto :create_venv
)

REM --- Download and install Python 3.11 silently ---
echo Python not found. Downloading Python 3.11...
echo (This may take a minute depending on your connection)
echo.

powershell -NoProfile -Command ^
    "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile 'python-installer.exe' -UseBasicParsing"

if not exist python-installer.exe (
    echo ERROR: Could not download Python. Check your internet connection and try again.
    pause
    exit /b 1
)

echo Installing Python 3.11 (no interaction needed)...
python-installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_launcher=0
del python-installer.exe

REM Give installer a moment to finish
timeout /t 3 /nobreak >nul

set PYTHON_EXE=%PYTHON_LOCAL%

if not exist "%PYTHON_EXE%" (
    echo ERROR: Python installation failed or installed to an unexpected location.
    echo Please install Python 3.11 manually from https://python.org and re-run this script.
    pause
    exit /b 1
)

echo Python 3.11 installed successfully.
echo.

:create_venv
echo Creating virtual environment...
"%PYTHON_EXE%" -m venv .venv

if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Failed to create virtual environment.
    pause
    exit /b 1
)

echo Installing dependencies (this may take a few minutes)...
echo.
.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
.venv\Scripts\pip.exe install PySide6 opencv-python pandas numpy

if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies. Check your internet connection and try again.
    pause
    exit /b 1
)

echo.
echo =============================================
echo   Setup complete!
echo   Double-click run.bat to start the app.
echo =============================================
echo.
pause
