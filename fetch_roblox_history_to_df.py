import requests
import sys
import json
import pandas as pd
from datetime import datetime

def fetch_chart_data(name, place_id, start, ends):
    url = (
        f"https://romonitorstats.com/api/v1/charts/get?name={name}"
        f"&placeId={place_id}"
        "&timeslice=day&proVersion=false&includeExperienceName=false"
        f"&start={start}&ends={ends}&anomalyDetection=true"
    )
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()

def extract_metric_data(json_data, metric_key):
    for entry in json_data:
        if entry.get('name', '').lower().startswith(metric_key):
            return entry['data']
    return {}

def main():
    if len(sys.argv) != 4:
        print("Usage: python fetch_roblox_history_to_df.py <placeId> <start_ISO8601> <ends_ISO8601>")
        print("Example: python fetch_roblox_history_to_df.py 126884695634066 2025-04-29T00:00:00.000Z 2025-05-12T23:59:59.999Z")
        sys.exit(1)
    place_id = sys.argv[1]
    start = sys.argv[2]
    ends = sys.argv[3]

    visits_json = fetch_chart_data('visits', place_id, start, ends)
    ccu_json = fetch_chart_data('ccus', place_id, start, ends)
    session_json = fetch_chart_data('session-length', place_id, start, ends)

    visits_data = extract_metric_data(visits_json, 'visits')
    ccu_data = extract_metric_data(ccu_json, 'ccu avg')
    session_data = extract_metric_data(session_json, 'session length')

    # Build dataframe
    all_dates = set()
    all_dates.update(visits_data.keys())
    all_dates.update(ccu_data.keys())
    all_dates.update(session_data.keys())
    all_dates = sorted(all_dates)

    rows = []
    for date in all_dates:
        date_only = date.split()[0] if date else None
        visits = visits_data.get(date)
        ccu = ccu_data.get(date)
        session = session_data.get(date)
        rows.append({
            'date': date_only,
            'visits': visits,
            'average_ccu': ccu,
            'session_length': session
        })

    df = pd.DataFrame(rows)
    df = df.sort_values('date').reset_index(drop=True)
    print(df)
    df.to_csv('roblox_history.csv', index=False)
    print("Saved to roblox_history.csv")

if __name__ == "__main__":
    main() 