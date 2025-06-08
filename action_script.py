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
    # The date is already added in scrape_bloxlink, so we don't need to do anything else here
    print("Discord activities scraping completed")

# 3. Scrape streamer data

def streamer_scrape_and_save():
    # Get DataFrame from streamer scraping
    df = streamer_main()
    
    if df is None:
        print("Warning: Streamer scraping failed, skipping streamer stats save")
        return
    
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
    try:
        main()
        asyncio.run(run_bloxlink_and_save())
        streamer_scrape_and_save()
    except Exception as e:
        print(f"Warning: An error occurred during execution: {str(e)}")
        print("Continuing with any successful data that was collected...")
        # Exit with success code since we handled the error
        exit(0) 