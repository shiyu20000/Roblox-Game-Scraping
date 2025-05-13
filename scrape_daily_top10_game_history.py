import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime, timedelta
import requests
import os
import subprocess

# This script fetches the top 10 Roblox games and their metrics (visits, average_ccu, session_length)
# for YESTERDAY (UTC), not today. It appends the results to roblox_top10_history.csv.
#
# Usage:
#   python scrape_daily_top10_game_history.py
#
# The script always fetches for the previous UTC day.

LEADERBOARD_URL = "https://romonitorstats.com/leaderboard/active/"
OUTPUT_CSV = "roblox_top10_history.csv"


def fetch_today_chart_data(name, place_id, date):
    start = f"{date}T00:00:00.000Z"
    ends = f"{date}T23:59:59.999Z"
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

def extract_metric_data(json_data, metric_key, date):
    for entry in json_data:
        if entry.get('name', '').lower().startswith(metric_key):
            # The key in data is the full datetime string
            for k, v in entry['data'].items():
                if k.startswith(date):
                    return v
    return None

async def scrape_top_games():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = await context.new_page()
        await page.goto(LEADERBOARD_URL)
        await page.wait_for_selector('table')
        await asyncio.sleep(3)
        rows = await page.query_selector_all('table tbody tr')
        games = []
        for rank, row in enumerate(rows[:10], start=1):
            cols = await row.query_selector_all('td')
            name_elem = await cols[2].query_selector('a')
            name = await name_elem.inner_text()
            url = await name_elem.get_attribute('href')
            if not url.startswith('http'):
                url = 'https://romonitorstats.com' + url
            game_id = url.rstrip('/').split('/')[-1]
            games.append({'ranking': rank, 'name': name, 'id': game_id})
        await browser.close()
        return games

def check_for_unknown_games(new_games, csv_path):
    if not os.path.exists(csv_path):
        return new_games
    history_df = pd.read_csv(csv_path)
    known_ids = set(history_df['id'].astype(str).unique())
    unknown_games = [g for g in new_games if str(g['id']) not in known_ids]
    return unknown_games

def main():
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    games = asyncio.run(scrape_top_games())
    unknown_games = check_for_unknown_games(games, OUTPUT_CSV)
    rows = []
    for game in games:
        place_id = game['id']
        visits_json = fetch_today_chart_data('visits', place_id, yesterday)
        ccu_json = fetch_today_chart_data('ccus', place_id, yesterday)
        session_json = fetch_today_chart_data('session-length', place_id, yesterday)
        visits = extract_metric_data(visits_json, 'visits', yesterday)
        average_ccu = extract_metric_data(ccu_json, 'ccu avg', yesterday)
        session_length = extract_metric_data(session_json, 'session length', yesterday)
        row = {
            'date': yesterday,
            'ranking': game['ranking'],
            'name': game['name'],
            'id': place_id,
            'visits': visits,
            'average_ccu': average_ccu,
            'session_length': session_length
        }
        rows.append(row)
    df = pd.DataFrame(rows)
    df = df[['date', 'ranking', 'name', 'id', 'visits', 'average_ccu', 'session_length']]

    if not unknown_games:
        # No new games, just append today's results
        write_header = not pd.io.common.file_exists(OUTPUT_CSV)
        df.to_csv(OUTPUT_CSV, mode='a', header=write_header, index=False)
        print(df)
        print(f"Saved to {OUTPUT_CSV}")
    else:
        print("Unknown games found, fetching 14-day history for each...")
        for game in unknown_games:
            # Calculate 14-day window ending yesterday
            start_date = (datetime.strptime(yesterday, "%Y-%m-%d") - timedelta(days=13)).strftime("%Y-%m-%dT00:00:00.000Z")
            end_date = f"{yesterday}T23:59:59.999Z"
            print(f"Fetching 14-day history for {game['name']} (id: {game['id']})")
            subprocess.run([
                'python', 'fetch_roblox_history_to_df.py',
                str(game['id']), start_date, end_date
            ], check=True)
            # Read the new game's history and append to main CSV
            new_df = pd.read_csv('roblox_history.csv')
            new_df['id'] = game['id']
            new_df['name'] = game['name']
            # Assign a temporary ranking (will be reranked)
            new_df['ranking'] = 99
            new_df = new_df[['date', 'ranking', 'name', 'id', 'visits', 'average_ccu', 'session_length']]
            write_header = not pd.io.common.file_exists(OUTPUT_CSV)
            new_df.to_csv(OUTPUT_CSV, mode='a', header=write_header, index=False)
        # Now append today's results as well
        df.to_csv(OUTPUT_CSV, mode='a', header=False, index=False)
        print(df)
        print(f"Appended new 14-day histories and today's results to {OUTPUT_CSV}")
        # Call rerank script to rerank all days
        print("Re-ranking all days...")
        subprocess.run(['python', 'rerank_top10_by_ccu.py'], check=True)
        print("Re-ranking complete.")

if __name__ == "__main__":
    main() 