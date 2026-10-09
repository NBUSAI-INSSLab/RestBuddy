@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PY=C:\Users\francis\.workbuddy\binaries\python\envs\restbuddy\Scripts\pythonw.exe
if not exist "%PY%" set PY=python
start "" "%PY%" "%~dp0main.py"
