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
    "formats": ["markdown"],
    "onlyMainContent": True,
    "waitFor": 5000
}

def clean_channel_name(val):
    match = re.match(r'\[([^\]]+)\]', val)
    if match:
        return match.group(1)
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

def to_number(val):
    return int(val.replace(" ", "").replace(",", ""))

def parse_markdown_table(md):
    """Extracts the streamer markdown table from the text and returns it as a list of dicts."""
    lines = md.splitlines()
    # Find the start of the table (header)
    header_idx = None
    for i, line in enumerate(lines):
        if (
            'Channel name' in line
            and 'Followers' in line
            and 'Hours Watched' in line
            and line.strip().startswith('|')
        ):
            header_idx = i
            break
    if header_idx is None:
        return []
    # Find the end of the table (first non-table line after header)
    table_lines = []
    for line in lines[header_idx:]:
        if not line.strip().startswith('|'):
            break
        table_lines.append(line)
    if len(table_lines) < 2:
        return []
    headers = [h.strip() for h in table_lines[0].split('|')[1:-1]]
    data = []
    for row in table_lines[2:]:
        cols = [c.strip() for c in row.split('|')[1:-1]]
        if len(cols) == len(headers):
            data.append(dict(zip(headers, cols)))
    return data

def main():
    response = requests.post(api_url, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        data = response.json()
        md = data.get('data', {}).get('markdown', '')
        if not md:
            print("No markdown content found in response.")
            return None
        table = parse_markdown_table(md)
        if table:
            df = pd.DataFrame(table)
            # Clean and select columns
            df['Name'] = df['Channel name'].apply(clean_channel_name)
            df['Followers'] = df['Followers'].apply(followers_to_number)
            df['Hours Watched'] = df['Hours Watched'].apply(to_number)
            df['Average Viewers'] = df['Average Viewers'].apply(to_number)
            df['Followers Gain'] = df['Followers Gain'].apply(to_number)
            # Sort by hours watched descending and assign rank
            df = df.sort_values('Hours Watched', ascending=False).reset_index(drop=True)
            df['Rank'] = df.index + 1
            # Select and reorder columns
            df = df[['Rank', 'Name', 'Followers', 'Hours Watched', 'Average Viewers', 'Followers Gain']]
            print(df)
            return df
        else:
            print("No table found in markdown.")
            return None
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

if __name__ == "__main__":
    main() 