@echo off
cd /d "%~dp0"
python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist config.ini copy config.ini.example config.ini
echo Setup finished. Run run.bat next.
pause
