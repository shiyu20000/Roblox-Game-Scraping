import os
import pandas as pd
import time
import asyncio
from datetime import datetime

from Youtube_scraping import get_top_10_most_viewed_videos
from search_query_cleaning import get_last_10_clean_names
from streatmer_scraping import main as streamer_main
from scrape_bloxlink_communities import scrape_bloxlink


def main():
    # Step 1: Get cleaned queries
    queries = get_last_10_clean_names()
    queries = [f"Roblox {q}" for q in queries]
    queries.insert(0, "Roblox")
    all_yt_rows = []
    all_trend_rows = []
    today = datetime.utcnow().strftime("%Y-%m-%d")
    for query in queries:
        print(f"\n=== Results for: {query} ===")
        # Step 2: YouTube scraping
        yt_results = get_top_10_most_viewed_videos(query)
        print(f"YouTube stats for '{query}':")
        for result in yt_results:
            print(f"  Mean Views: {result['mean_views']}")
            print(f"  Mean Likes: {result['mean_likes']}")
        # Store YouTube results
        for result in yt_results:
            all_yt_rows.append({
                'date': today,
                'query': query,
                'mean_views': result['mean_views'],
                'mean_likes': result['mean_likes']
            })
        # No Google Trends data needed
        time.sleep(1)  # Small delay between YouTube requests
    # Save to CSVs
    yt_df = pd.DataFrame(all_yt_rows)
    # Ensure date is the first column
    cols = ['date'] + [col for col in yt_df.columns if col != 'date']
    yt_df = yt_df[cols]
    yt_csv = 'youtube_results.csv'
    if os.path.exists(yt_csv):
        yt_df.to_csv(yt_csv, mode='a', header=False, index=False)
    else:
        yt_df.to_csv(yt_csv, index=False)
    print(f"Saved/appended YouTube results to {yt_csv}")


# 2. Scrape bloxlink (async)
async def run_bloxlink_and_save():
    await scrape_bloxlink()
    # After running, load the daily average CSV and save as Roblox_discord_activities.csv
    out_csv = 'Roblox_discord_activities.csv'
    if os.path.exists(out_csv):
        df = pd.read_csv(out_csv)
        # Add today's date
        today = datetime.utcnow().strftime("%Y-%m-%d")
        df['date'] = today
        df.to_csv(out_csv, index=False)
        print(f"Saved Roblox Discord activities to {out_csv}")
    else:
        print(f"{out_csv} not found after scraping.")

# 3. Scrape streamer data

def streamer_scrape_and_save():
    # Get DataFrame from streamer scraping
    df = streamer_main()
    
    # Add today's date column
    today = datetime.utcnow().strftime("%Y-%m-%d")
    df['date'] = today
    
    # Ensure date is the first column
    cols = ['date'] + [col for col in df.columns if col != 'date']
    df = df[cols]
    
    # Save to CSV
    out_csv = 'streamer_stats.csv'
    if os.path.exists(out_csv):
        df.to_csv(out_csv, mode='a', header=False, index=False)
    else:
        df.to_csv(out_csv, index=False)
    print(f"Saved/appended streamer stats to {out_csv}")


if __name__ == "__main__":
    main()
    asyncio.run(run_bloxlink_and_save())
    streamer_scrape_and_save() 