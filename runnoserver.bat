@echo off
cd /d "%~dp0"

echo Running Strava data pull...
python strava_data_pull.py

echo Building HTML...
python build_html.py

echo DONE

pause