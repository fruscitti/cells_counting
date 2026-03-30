@echo off

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found.
    echo Please run setup.bat first.
    pause
    exit /b 1
)

.venv\Scripts\python.exe app.py
