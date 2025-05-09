import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import time
from datetime import datetime
import os

LEADERBOARD_URL = "https://romonitorstats.com/leaderboard/active/"
CSV_FILE = "roblox_game_stats.csv"

async def scrape_top_games():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = await context.new_page()
        await page.goto(LEADERBOARD_URL)
        await page.wait_for_selector('table')
        await asyncio.sleep(3)  # Give time for dynamic content

        # Scrape the top 10 game links from the leaderboard table
        rows = await page.query_selector_all('table tbody tr')
        games = []
        for row in rows[:10]:
            cols = await row.query_selector_all('td')
            name_elem = await cols[2].query_selector('a')
            name = await name_elem.inner_text()
            url = await name_elem.get_attribute('href')
            if not url.startswith('http'):
                url = 'https://romonitorstats.com' + url
            concurrent_users = (await cols[3].inner_text()).replace(",", "").strip()
            visits = (await cols[4].inner_text()).replace(",", "").strip()
            games.append({'name': name, 'url': url, 'concurrent_users': int(concurrent_users), 'visits': visits})

        # For each game, click and scrape details
        for game in games:
            await page.goto(game['url'])
            await page.wait_for_selector('body')
            await asyncio.sleep(2)
            # Scrape average session time
            try:
                h5s = await page.query_selector_all('h5')
                session_time = None
                for h5 in h5s:
                    text = await h5.inner_text()
                    if "Session Length" in text:
                        h1 = await h5.evaluate_handle('el => el.nextElementSibling')
                        if h1:
                            session_time = await h1.inner_text()
                            session_time = session_time.replace('Minutes', '').strip()
                        break
            except Exception:
                session_time = None
            game['average_session_time'] = session_time
            if session_time is None or session_time == '':
                with open('scraper.log', 'a') as logf:
                    logf.write(f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] Missing average_session_time for {game['name']} ({game['url']}) on {datetime.utcnow().strftime('%Y-%m-%d')}\n")
            time.sleep(1)
        await browser.close()
        return games

def main():
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    games = asyncio.run(scrape_top_games())
    for game in games:
        game['date'] = date_str
    df = pd.DataFrame(games)
    # Rank by concurrent_users (descending) for this day
    df['daily_rank'] = df['concurrent_users'].rank(method='first', ascending=False).astype(int)
    # Reorder columns: date, daily_rank, name, url, concurrent_users, visits, average_session_time
    df = df[['date', 'daily_rank', 'name', 'url', 'concurrent_users', 'visits', 'average_session_time']]

    # Calculate incremental visits for days after the first day
    if os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 0:
        prev_df = pd.read_csv(CSV_FILE)
        prev_df['date'] = prev_df['date'].astype(str)
        prev_df = prev_df.sort_values(['name', 'url', 'date'])
        # Get the last available visits for each game
        last_visits = prev_df.groupby(['name', 'url'])['visits'].last().to_dict()
        for idx, row in df.iterrows():
            key = (row['name'], row['url'])
            try:
                prev_visits = int(last_visits[key])
                curr_visits = int(row['visits'])
                df.at[idx, 'visits'] = curr_visits - prev_visits
            except (KeyError, ValueError):
                # If no previous visits or conversion error, keep as is
                pass

    # Append to CSV, create with header if not exists, handle empty file
    write_header = not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) == 0
    df.to_csv(CSV_FILE, mode='a', header=write_header, index=False)
    print(df)

if __name__ == "__main__":
    main()

# --- Scheduling Instructions ---
"""
To run this script daily:
- On macOS/Linux: Add to your crontab (crontab -e):
  0 2 * * * /path/to/python3 /path/to/Scraper.py
- On Windows: Use Task Scheduler to run 'python Scraper.py' daily.
"""
