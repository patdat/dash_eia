@echo off
call .venv\Scripts\activate
start chrome http://localhost:8052
python run.py
pause
