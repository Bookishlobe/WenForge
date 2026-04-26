@echo off
cd /d "%~dp0"
python -m uvicorn main:app --host 127.0.0.1 --port 8765 > "%~dp0..\python.log" 2>&1
exit
