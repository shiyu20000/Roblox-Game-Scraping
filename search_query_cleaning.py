import pandas as pd
import re

def clean_name(name):
    # Remove content within []
    name = re.sub(r'\[.*?\]', '', name)
    # Remove emojis (unicode ranges for emojis)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002700-\U000027BF"  # Dingbats
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U00002600-\U000026FF"  # Misc symbols
        "\U00002B50-\U00002B55"  # Stars
        "\U00002300-\U000023FF"  # Misc technical
        "]+",
        flags=re.UNICODE)
    name = emoji_pattern.sub(r'', name)
    # Remove extra whitespace and spaces before/after game name
    name = name.strip()
    # Remove multiple spaces between words
    name = ' '.join(name.split())
    return name

def get_last_10_clean_names(csv_path='roblox_top10_history.csv'):
    df = pd.read_csv(csv_path)
    last_10 = df.tail(10)
    names = last_10['name'].tolist()
    clean_names = [clean_name(n) for n in names]
    return clean_names

# Store clean names in a list for future use
clean_names = []
if __name__ == "__main__":
    clean_names = get_last_10_clean_names()
    print("Last 10 clean search queries:")
    for q in clean_names:
        print(q)
