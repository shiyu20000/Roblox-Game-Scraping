import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime, timedelta
import subprocess
import json
import os

LEADERBOARD_URL = "https://romonitorstats.com/leaderboard/active/"
DAYS = 14
OUTPUT_CSV = "roblox_top10_history.csv"

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

def fetch_history_for_game(place_id, start, ends):
    # Call fetch_roblox_history_to_df.py and capture its output CSV
    temp_csv = f"temp_{place_id}.csv"
    cmd = [
        'python', 'fetch_roblox_history_to_df.py',
        str(place_id), start, ends
    ]
    env = os.environ.copy()
    env['OUTPUT_CSV'] = temp_csv
    subprocess.run(cmd, check=True, env=env)
    df = pd.read_csv('roblox_history.csv')
    return df

def main():
    # Get date range for the last 14 days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=DAYS-1)
    start_iso = start_date.strftime("%Y-%m-%dT00:00:00.000Z")
    end_iso = end_date.strftime("%Y-%m-%dT23:59:59.999Z")

    games = asyncio.run(scrape_top_games())
    all_rows = []
    for game in games:
        df = fetch_history_for_game(game['id'], start_iso, end_iso)
        df['ranking'] = game['ranking']
        df['name'] = game['name']
        df['id'] = game['id']
        all_rows.append(df)
    combined = pd.concat(all_rows, ignore_index=True)
    combined = combined[['date', 'ranking', 'name', 'id', 'visits', 'average_ccu', 'session_length']]
    combined = combined.sort_values(['date', 'ranking']).reset_index(drop=True)
    print(combined)
    combined.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    main() 