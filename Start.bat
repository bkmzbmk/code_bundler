@echo off
cd /d "%~dp0"

REM Полный путь к pythonw из Anaconda (без консоли)
start "" "C:\ProgramData\anaconda3\pythonw.exe" main.py

REM Для отладки (с консолью):
REM "C:\ProgramData\anaconda3\python.exe" main.py