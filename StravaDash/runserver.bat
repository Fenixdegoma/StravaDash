@echo off
cd /d "%~dp0"

echo Running Strava data pull...
python strava_data_pull.py

echo Building HTML...
python build_html.py

echo Starting local server...
cd dashboard
python -m http.server 8000

pause