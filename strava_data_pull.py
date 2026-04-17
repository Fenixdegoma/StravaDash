import os
import time
import json
import requests
import sqlite3
from datetime import datetime

DB = "strava.db"
OUT = "dashboard"

CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")

RIDE_TYPES = {"Ride", "VirtualRide", "MountainBikeRide", "EMountainBikeRide", "GravelRide"}
STREAM_KEYS = ["distance","time","moving","altitude","latlng"]  # add more if needed

# -------------------------
# AUTH
# -------------------------
def get_access_token():
    res = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": REFRESH_TOKEN,
            "grant_type": "refresh_token"
        }
    )
    data = res.json()
    if "access_token" not in data:
        raise Exception("Auth failed")
    return data["access_token"]

# -------------------------
def safe_get(url, token, params=None):
    res = requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params)
    data = res.json()
    if isinstance(data, dict) and "message" in data:
        if "Rate Limit" in data["message"]:
            time.sleep(60)
            return safe_get(url, token, params)
        return None
    return data

# -------------------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY,
        name TEXT,
        type TEXT,
        distance REAL,
        elevation REAL,
        moving_time INTEGER,
        start_date TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS activity_streams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        activity_id INTEGER,
        type TEXT,
        data TEXT,
        FOREIGN KEY(activity_id) REFERENCES activities(id)
    )
    """)
    conn.commit()
    conn.close()

# -------------------------
def get_latest_activity_time():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT MAX(start_date) FROM activities")
    latest = c.fetchone()[0]
    conn.close()
    if latest:
        dt = datetime.fromisoformat(latest.replace("Z",""))
        return int(dt.timestamp())
    return None

# -------------------------
def fetch_activities(token, after=None):
    page = 1
    all_acts = []
    while True:
        params = {"per_page": 200, "page": page, "order": "asc"}
        if after:
            params["after"] = after
        data = safe_get(
            "https://www.strava.com/api/v3/athlete/activities",
            token,
            params
        )
        if not data:
            break
        rides = [a for a in data if a.get("sport_type") in RIDE_TYPES]
        all_acts.extend(rides)
        if len(data) < 200:
            break
        page += 1
        time.sleep(1)
    return all_acts

# -------------------------
def fetch_streams(token, activity_id):
    data = safe_get(
        f"https://www.strava.com/api/v3/activities/{activity_id}/streams",
        token,
        params={"keys": ",".join(STREAM_KEYS), "key_by_type": True}
    )
    return data or {}

def store_activities(acts, token):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    for a in acts:
        c.execute("""
        INSERT OR REPLACE INTO activities VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            a["id"],
            a.get("name"),
            a.get("sport_type"),
            a.get("distance",0)/1000,
            a.get("total_elevation_gain",0),
            a.get("moving_time",0),
            a.get("start_date")
        ))
        # store streams separately
        streams = fetch_streams(token, a["id"])
        for k,v in streams.items():
            if isinstance(v, dict) and "data" in v:
                c.execute("""
                INSERT INTO activity_streams (activity_id, type, data) VALUES (?, ?, ?)
                """, (a["id"], k, json.dumps(v["data"])))
        time.sleep(0.5)  # avoid hitting rate limit
    conn.commit()
    conn.close()

# -------------------------
def fmt_month(date_str):
    dt = datetime.fromisoformat(date_str.replace("Z",""))
    return dt.strftime("%b-%y")

def fmt_day(date_str):
    dt = datetime.fromisoformat(date_str.replace("Z",""))
    return dt.strftime("%d-%b-%y")

# -------------------------
def compute_fastest_from_streams(c, km):
    """Compute top 10 fastest times over given km using distance/time streams."""
    top10 = []
    c.execute("SELECT id FROM activities WHERE distance >= ?", (km,))
    for (activity_id,) in c.fetchall():
        c.execute("SELECT type,data FROM activity_streams WHERE activity_id=?", (activity_id,))
        streams = {row[0]: json.loads(row[1]) for row in c.fetchall()}
        if "distance" in streams and "time" in streams:
            dist_list = streams["distance"]
            time_list = streams["time"]
            best_sec = None
            for i in range(len(dist_list)):
                for j in range(i+1, len(dist_list)):
                    delta_dist = dist_list[j]-dist_list[i]
                    if delta_dist >= km*1000:
                        delta_time = time_list[j]-time_list[i]
                        if best_sec is None or delta_time < best_sec:
                            best_sec = delta_time
                        break
            if best_sec:
                c.execute("SELECT start_date FROM activities WHERE id=?", (activity_id,))
                start_date = c.fetchone()[0]
                top10.append((start_date, best_sec))
    top10.sort(key=lambda x:x[1])
    return top10[:5]
    
def extract_climbs(altitudes, distances):
    """
    Strava-style climb detection:
    - Tracks climb from start to peak
    - Allows up to 25% drop from peak
    - Ends climb when drop exceeds 25%
    Returns climbs as (gain_m, distance_m, gradient_pct, score)
    """
    climbs = []

    start_idx = None
    start_alt = None
    max_alt = None

    for i in range(1, len(altitudes)):
        alt = altitudes[i]

        if start_idx is None:
            start_idx = i - 1
            start_alt = altitudes[start_idx]
            max_alt = start_alt

        # update peak altitude
        if alt > max_alt:
            max_alt = alt

        gain = max_alt - start_alt
        drop = max_alt - alt

        allowed_drop = gain * 0.25 if gain > 0 else 0

        # if drop too big → climb ends
        if drop > allowed_drop:
            end_idx = i - 1

            climb_gain = max_alt - start_alt
            climb_dist = distances[end_idx] - distances[start_idx]

            if climb_gain > 0 and climb_dist > 0:
                gradient = (climb_gain / climb_dist) * 100
                score = climb_dist * gradient

              
                climbs.append((climb_gain, climb_dist, gradient, score))

            # reset
            start_idx = None
            start_alt = None
            max_alt = None

    # catch climb at end
    if start_idx is not None:
        climb_gain = max_alt - start_alt
        climb_dist = distances[-1] - distances[start_idx]

        if climb_gain > 0 and climb_dist > 0:
            gradient = (climb_gain / climb_dist) * 100
            score = climb_dist * gradient

           
            climbs.append((climb_gain, climb_dist, gradient, score))

    return climbs


def categorize_climb(score):
    if score > 80000:
        return 'HC'
    elif score > 64000:
        return 'Cat1'
    elif score > 32000:
        return 'Cat2'
    elif score > 16000:
        return 'Cat3'
    elif score > 8000:
        return 'Cat4'
    else:
        return ''


def compute_biggest_climbs(c):
    """
    Extract climbs using Strava scoring.
    Returns top 5 climbs sorted by score (not gain).
    """
    all_climbs = []

    c.execute("SELECT id, start_date FROM activities")
    for activity_id, start_date in c.fetchall():
        c.execute("SELECT type,data FROM activity_streams WHERE activity_id=?", (activity_id,))
        streams = {row[0]: json.loads(row[1]) for row in c.fetchall()}

        if "altitude" in streams and "distance" in streams:
            altitudes = streams["altitude"]
            distances = streams["distance"]

            if len(altitudes) != len(distances):
                continue

            climbs = extract_climbs(altitudes, distances)

            for gain, dist, grad, score in climbs:
                cat = categorize_climb(score)

                all_climbs.append((start_date, gain, dist, grad, score, cat))

    # ⚠️ THIS is the real change
    all_climbs.sort(key=lambda x: x[4], reverse=True)

    result = []
    for d, gain, dist, grad, score, cat in all_climbs[:5]:
        result.append({
            "date": fmt_day(d),
            "gain_m": round(gain, 1),
            "distance_m": round(dist, 1),
            "gradient_pct": round(grad, 1),
            "score": int(score),
            "category": cat
        })

    return result
    
# -------------------------
def compute_stats():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Summary
    c.execute("SELECT COUNT(*), SUM(distance), SUM(elevation), SUM(moving_time) FROM activities")
    total_rides, total_distance, total_elevation, total_time = c.fetchone()
    total_distance = total_distance or 0
    total_elevation = total_elevation or 0
    total_time = total_time or 0
    avg_pace_sec = (total_time / total_distance) if total_distance else 0

    # Active days
    year = datetime.now().strftime("%Y")
    c.execute("""SELECT COUNT(DISTINCT substr(start_date,1,10)) FROM activities WHERE substr(start_date,1,4)=?""", (year,))
    active_days = c.fetchone()[0] or 0
    days_passed = (datetime.now() - datetime(datetime.now().year,1,1)).days + 1
    rest_days = days_passed - active_days

    # Monthly
    c.execute("""SELECT substr(start_date,1,7), COUNT(*), SUM(distance) FROM activities GROUP BY substr(start_date,1,7) ORDER BY substr(start_date,1,7) DESC LIMIT 12""")
    monthly_rows = c.fetchall()
    monthly_rows.reverse()

    # Top tables
    def get_top(query):
        c.execute(query)
        return [{"date": fmt_day(r[0]), "value": r[1]} for r in c.fetchall()]

    top_longest = get_top("SELECT start_date, distance FROM activities ORDER BY distance DESC LIMIT 5")
    top_climbs = compute_biggest_climbs(c)

    thresholds = [1,5,10,25,50]
    fastest = []
    for km in thresholds:
        rows = compute_fastest_from_streams(c, km)
        if rows:
            fastest.append({
                "label": f"Fastest {km} km",
                "rows": [{"date": fmt_day(r[0]), "value": r[1]} for r in rows]
            })

    # -------------------------
    # Build calendar/daily totals for current year
    c.execute("""
        SELECT substr(start_date,1,10) AS day, SUM(distance) 
        FROM activities 
        WHERE substr(start_date,1,4)=?
        GROUP BY day
    """, (year,))
    daily_totals = {row[0]: row[1] for row in c.fetchall()}  # key = YYYY-MM-DD, value = total distance km

    # Maximum single-day distance (for scaling)
    max_daily_distance = max(daily_totals.values()) if daily_totals else 0

    # -------------------------
    # Build stats dict
    stats = {
        "summary": {
            "total_rides": total_rides,
            "total_distance": total_distance,
            "total_elevation": total_elevation,
            "total_time": total_time,
            "avg_pace_sec": avg_pace_sec,
            "active_days": active_days,
            "rest_days": rest_days
        },
        "monthly": {
            "labels": [fmt_month(r[0]+"-01") for r in monthly_rows],
            "rides": [r[1] for r in monthly_rows],
            "distance": [r[2] for r in monthly_rows]
        },
        "top_longest": top_longest,
        "top_climbs": top_climbs,
        "fastest": fastest,
        "daily_totals": daily_totals,
        "max_daily_distance": max_daily_distance
    }

    # Elevation brag gimmick
    elev_file = os.path.join(OUT, "elevation.json")
    brag_item = None
    next_target = None
    elev_data_list = []
    if os.path.exists(elev_file):
        with open(elev_file, "r", encoding="utf-8") as f:
            elev_data_list = json.load(f)
        # sort descending
        elev_data_list.sort(key=lambda x: x["height_m"], reverse=True)
        total_elev = total_elevation or 0
        # find highest beaten
        for item in elev_data_list:
            if total_elev > item["height_m"]:
                brag_item = f"You've climbed higher than {item['name']} ({item['height_m']} m)"
                break
        # find next target (first higher)
        for item in reversed(elev_data_list):  # from smallest to largest
            if item["height_m"] > total_elev:
                next_target = f"Next target: {item['name']} ({item['height_m']} m)"
                break

    stats["elevation_brag"] = brag_item
    stats["elevation_target"] = next_target
    stats["elevation_data"] = elev_data_list  # optional, in case JS wants full list
    
    return stats

# -------------------------
def fetch_athlete(token):
    data = safe_get("https://www.strava.com/api/v3/athlete", token)
    if not data:
        return {"firstname": "", "lastname": ""}
    return {"firstname": data.get("firstname",""), "lastname": data.get("lastname","")}

# -------------------------
def main():
    token = get_access_token()
    init_db()
    latest_epoch = get_latest_activity_time()
    acts = fetch_activities(token, after=latest_epoch)
    store_activities(acts, token)

    stats = compute_stats()            # compute stats dict
    athlete = fetch_athlete(token)     # fetch athlete info
    stats["athlete"] = athlete         # add to stats

    os.makedirs(OUT, exist_ok=True)
    with open(f"{OUT}/stats.json","w") as f:
        json.dump(stats, f, indent=2)

    print('Data updated.\nNow run: python build_html.py')

if __name__=="__main__":
    main()