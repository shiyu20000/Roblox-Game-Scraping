import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime

BASE_URL = "https://blox.link/communities/search?page={}"

RETRIES = 3
WAIT_BETWEEN_RETRIES = 5  # seconds
PAGE_WAIT = 30  # seconds to wait for page load
SELECTOR_WAIT = 30  # seconds to wait for selector

def parse_member_count(member_str):
    # Remove non-numeric and non-K/M characters
    member_str = member_str.replace('Members', '').replace('Member', '').strip()
    match = re.match(r"([\d.]+)([KM]?)", member_str)
    if not match:
        return 0
    num, suffix = match.groups()
    num = float(num)
    if suffix == 'K':
        num *= 1_000
    elif suffix == 'M':
        num *= 1_000_000
    return num

async def scrape_bloxlink():
    communities = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://blox.link/"
            }
        )
        page = await context.new_page()
        for page_num in range(1, 11):  # Pages 1 to 10
            url = BASE_URL.format(page_num)
            success = False
            for attempt in range(RETRIES):
                try:
                    print(f"Scraping {url} (attempt {attempt+1})...")
                    await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_WAIT * 1000)
                    await asyncio.sleep(3)  # Let dynamic content load
                    content = await page.content()
                    if "Just a moment..." in content or "Verifying you are human" in content:
                        print(f"Blocked by Cloudflare on {url}")
                        break
                    await page.wait_for_selector("a[href^='/communities/']", timeout=SELECTOR_WAIT * 1000)
                    html = await page.content()
                    soup = BeautifulSoup(html, "html.parser")
                    for card in soup.select("a[href^='/communities/']:not([href*='/tag/'])"):
                        # Name
                        name_elem = card.select_one("p.text-xl.font-bold")
                        name = name_elem.get_text(strip=True) if name_elem else ""
                        # Members & Upvotes
                        stats = card.select("div.flex.gap-2.z-40 > p")
                        members = stats[0].get_text(strip=True) if len(stats) > 0 else ""
                        upvotes = stats[1].get_text(strip=True) if len(stats) > 1 else ""
                        # Description
                        desc_elem = card.select_one("p.text-sm.font-normal.text-primary-text.text-left.line-clamp-2")
                        description = desc_elem.get_text(strip=True) if desc_elem else ""
                        # Tags
                        tags = [tag.get_text(strip=True) for tag in card.select("div.bg-indigo-600.text-white.py-1.px-2.font-medium.text-xs.rounded-md")]
                        communities.append({
                            "name": name,
                            "members": members,
                            "upvotes": upvotes,
                            "description": description,
                            "tags": ", ".join(tags)
                        })
                    success = True
                    break  # Success, break out of retry loop
                except PlaywrightTimeoutError as e:
                    print(f"Timeout error on {url} (attempt {attempt+1}): {e}")
                    await asyncio.sleep(WAIT_BETWEEN_RETRIES)
                except Exception as e:
                    print(f"Error scraping {url} (attempt {attempt+1}): {e}")
                    await asyncio.sleep(WAIT_BETWEEN_RETRIES)
            if not success:
                print(f"Failed to scrape {url} after {RETRIES} attempts. Skipping.")
        await browser.close()

    df = pd.DataFrame(communities)

    # Calculate average member number
    if not df.empty:
        df['member_num'] = df['members'].apply(parse_member_count)
        avg_members = df['member_num'].mean()
        print(f"Average member number across all channels: {avg_members:.2f}")
    else:
        avg_members = 0
        print("No communities scraped.")

    # Save to daily average CSV
    today = datetime.utcnow().strftime("%Y-%m-%d")
    avg_df = pd.DataFrame([[today, avg_members]], columns=["date", "Avg_discord_member_per_channel"])
    avg_csv = "Roblox_discord_activities.csv"
    try:
        existing = pd.read_csv(avg_csv)
        avg_df = pd.concat([existing, avg_df], ignore_index=True)
        avg_df = avg_df.drop_duplicates(subset=["date"], keep="last")
    except FileNotFoundError:
        pass
    avg_df.to_csv(avg_csv, index=False)
    print(f"Saved daily average to {avg_csv}")

if __name__ == "__main__":
    asyncio.run(scrape_bloxlink())
