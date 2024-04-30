@echo off
call "venv\Scripts\activate.bat"
cd /d "%~dp0"
start "" "venv\Scripts\pythonw.exe" "main.py"