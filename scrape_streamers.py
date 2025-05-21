import requests
import json
import pandas as pd
import re

FIRECRAWL_API_KEY = "fc-b48091786e1d45ec886821eea63c77b3"  # Replace with your Firecrawl API key
url = "https://streamscharts.com/channels?game=roblox"

api_url = "https://api.firecrawl.dev/v1/scrape"
headers = {
    "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
    "Content-Type": "application/json"
}
payload = {
    "url": url,
    "formats": ["markdown"],  # You can also use "extract" for structured data
    "waitFor": 15000  # 15 seconds
}

def parse_markdown_table(md):
    lines = md.splitlines()
    table_lines = []
    in_table = False
    for line in lines:
        if line.strip().startswith('|') and '---' not in line:
            table_lines.append(line.strip())
            in_table = True
        elif in_table and not line.strip().startswith('|'):
            break
    if len(table_lines) < 2:
        return []
    headers = [h.strip().lower() for h in table_lines[0].split('|')[1:-1]]
    data = []
    for row in table_lines[2:]:
        cols = [c.strip() for c in row.split('|')[1:-1]]
        if len(cols) == len(headers):
            data.append(dict(zip(headers, cols)))
    return data

def clean_channel_name(val):
    # Extract plain text from markdown link: [name](url)
    match = re.match(r'\[([^\]]+)\]', val)
    if match:
        return match.group(1)
    # Remove any brackets or parentheses
    return re.sub(r'\[.*?\]|\(.*?\)', '', val).strip()

def followers_to_number(val):
    val = val.replace(",", "").strip()
    if val.endswith('M'):
        return int(float(val[:-1]) * 1_000_000)
    elif val.endswith('K'):
        return int(float(val[:-1]) * 1_000)
    else:
        try:
            return int(val)
        except ValueError:
            return None

response = requests.post(api_url, headers=headers, data=json.dumps(payload))
if response.status_code == 200:
    data = response.json()
    md = data.get('data', {}).get('markdown', '')
    if not md:
        print("No markdown content found in response.")
    else:
        table = parse_markdown_table(md)
        if table:
            df = pd.DataFrame(table)
            print("Raw DataFrame head for debugging:")
            print(df.head())
            # Always use the first column as 'Rank'
            cols = list(df.columns)
            rank_col = cols[0]
            # Automatically select the column with the most markdown links as 'Channel Name'
            markdown_link_pattern = re.compile(r'\[.*?\]\(.*?\)')
            max_links = 0
            channel_col = None
            for c in df.columns:
                count = df[c].astype(str).str.count(markdown_link_pattern).sum()
                if count > max_links:
                    max_links = count
                    channel_col = c
            # Try to find the best matching columns for the rest
            col_map = {
                'followers': ["followers"],
                'hours watched': ["hours watched", "watched hours"],
                'average viewers': ["average viewers"]
            }
            col_lc_to_orig = {c.lower(): c for c in df.columns}
            selected = {'rank': rank_col, 'channel name': channel_col}
            for key, possibles in col_map.items():
                for p in possibles:
                    for c in col_lc_to_orig:
                        if p in c:
                            selected[key] = col_lc_to_orig[c]
                            break
                    if key in selected:
                        break
            required = ['rank', 'channel name', 'followers', 'hours watched']
            if all(k in selected for k in required):
                out_cols = [selected['rank'], selected['channel name'], selected['followers'], selected['hours watched']]
                if 'average viewers' in selected:
                    out_cols.append(selected['average viewers'])
                df = df[out_cols]
                # Rename columns
                new_names = ['Rank', 'Channel Name', 'Followers', 'Hours Watched']
                if 'average viewers' in selected:
                    new_names.append('Average Viewers')
                df.columns = new_names
                # Clean channel name
                df['Channel Name'] = df['Channel Name'].apply(clean_channel_name)
                # Convert followers to numbers
                df['Followers'] = df['Followers'].apply(followers_to_number)
                print("Final DataFrame head:")
                print(df.head(10))
                print(df)
            else:
                print("Could not find all required columns in the table.")
                print("DataFrame head for debugging:")
                print(df.head())
        else:
            print("No table found in markdown.")
        with open('scraped_markdown.md', 'w', encoding='utf-8') as f:
            f.write(md)
else:
    print("Error:", response.status_code, response.text) 