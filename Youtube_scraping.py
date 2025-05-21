import requests
import pandas as pd
import re

API_KEY = "AIzaSyAGZwJm-c1slQGM54bzEl2OmKlOouNQEAo"


def get_top_10_most_viewed_videos(search_query):
    search_url = "https://www.googleapis.com/youtube/v3/search"
    search_params = {
        "part": "snippet",
        "q": search_query,
        "key": API_KEY,
        "maxResults": 10,
        "type": "video",
        "order": "viewCount"
    }

    search_response = requests.get(search_url, params=search_params)
    search_data = search_response.json()

    video_ids = [item["id"]["videoId"] for item in search_data.get("items", [])]

    if video_ids:
        video_url = "https://www.googleapis.com/youtube/v3/videos"
        video_params = {
            "part": "snippet,statistics",
            "id": ",".join(video_ids),
            "key": API_KEY
        }
        video_response = requests.get(video_url, params=video_params)
        video_data = video_response.json()

        total_views = 0
        total_likes = 0
        video_count = 0
        
        for item in video_data.get("items", []):
            stats = item.get("statistics", {})
            views = stats.get("viewCount", "N/A")
            likes = stats.get("likeCount", "N/A")
            
            # Add to totals if both views and likes are available
            if views != "N/A" and likes != "N/A":
                total_views += int(views)
                total_likes += int(likes)
                video_count += 1

        # Calculate means
        if video_count > 0:
            mean_views = total_views / video_count
            mean_likes = total_likes / video_count
            return [{
                "game": search_query,
                "mean_views": mean_views,
                "mean_likes": mean_likes
            }]
        else:
            return [{
                "game": search_query,
                "mean_views": 0,
                "mean_likes": 0
            }]
    else:
        print("No videos found.")
        return [{
            "game": search_query,
            "mean_views": 0,
            "mean_likes": 0
        }]





if __name__ == "__main__":
    # Example usage for Roblox
    query = "Roblox"
    results = get_top_10_most_viewed_videos(query)
    for result in results:
        print(f"Game: {result['game']}")
        print(f"Mean Views: {result['mean_views']}")
        print(f"Mean Likes: {result['mean_likes']}\n")
