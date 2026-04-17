# Strava Dashboard

A lightweight Python tool that pulls your Strava activity data, stores it locally, and generates a static interactive dashboard (charts, stats, and heatmap).

---

## Features

- Total ride stats (distance, elevation, time)
- Monthly distance and ride charts
- Top rides and climbs tables
- Fastest segment approximations (via streams)
- Yearly activity heatmap
- Local static dashboard (no backend required)

---

## Requirements

- Python 3.8+
- A Strava API application
- Internet connection (for Strava API access)

---

## Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# Strava API Setup

You must create a Strava API application to access your data.

---

## Step 1 — Create an application

Go to:

https://www.strava.com/settings/api

Click **Create Application** and fill in:

- Application Name: anything (e.g. "Strava Dashboard")
- Website: http://localhost
- Authorization Callback Domain: localhost

Save it and note:

- Client ID
- Client Secret

---

## Step 2 — Authentication (Recommended Method)

This project includes an automated authentication helper script:

```bash
python getauth.py
```

---

### What you do

1. Run the script
2. Enter your:
   - Client ID
   - Client Secret
3. Open the URL that is displayed
4. Authorise the application in Strava
5. You will be redirected to a URL
6. **Copy the ENTIRE redirect URL from your browser**
7. Paste it into the script when prompted

---

### Important

✔ You do NOT need to extract any code manually  
✔ Do NOT try to find `code=` or edit the URL  
✔ Just paste the full redirect URL  

Example:

```
http://localhost/?code=ABC123XYZ&scope=activity:read_all
```

---

### What the script does automatically

- Extracts the authorisation code from the URL
- Exchanges it for a Strava refresh token
- Saves credentials locally in `strava_auth.txt`
- Optionally sets Windows environment variables (`setx`)

---

## Output

After running `getauth.py`, you will have:

### File created:
```
strava_auth.txt
```

Contains:
- client_id
- client_secret
- refresh_token

---

## Windows note

If `setx` is used, you may need to restart your terminal for changes to apply.

---

# Running the Dashboard

This project includes a Windows automation script:

```bash
runserver.bat
```

---

## What it does

When run, `runserver.bat` will:

1. Pull the latest Strava activity data (`strava_data_pull.py`)
2. Store/update the local SQLite database
3. Build the dashboard HTML (`build_html.py`)
4. Start a local web server on port 8000

---

## How to use

After completing authentication:

### 1. Run full pipeline

Double-click:

```
runserver.bat
```

or run in terminal:

```
runserver.bat
```

---

### 2. Open dashboard

Once complete, open:

```
http://localhost:8000/index.html
```

---

## Typical workflow

1. Run `getauth.py` (first time only)
2. Run `runserver.bat` whenever you want updated data
3. Open the dashboard in your browser

---

## Important Notes

- The pipeline must complete successfully before opening the dashboard
- If data does not update, re-run `runserver.bat`
- If port 8000 is already in use:
  ```
  taskkill /F /IM python.exe
  ```
- If you reach Strava API limits, simply re-run later — the script will only fetch new activities once fully synced
- Do not manually edit files inside `/dashboard`