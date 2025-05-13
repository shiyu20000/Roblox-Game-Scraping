import pandas as pd

# Load the top 10 history CSV
csv_file = 'roblox_top10_history.csv'
df = pd.read_csv(csv_file)

# Deduplicate by (date, id), keeping the row with the highest average_ccu
df = df.sort_values(['date', 'id', 'average_ccu'], ascending=[True, True, False])
df = df.drop_duplicates(subset=['date', 'id'], keep='first')

# Rerank by average_ccu for each day
def rerank_group(group):
    group = group.copy()
    group = group.sort_values('average_ccu', ascending=False)
    group['ranking'] = range(1, len(group) + 1)
    return group

reranked_df = df.groupby('date', group_keys=False).apply(rerank_group)
reranked_df = reranked_df.sort_values(['date', 'ranking']).reset_index(drop=True)

# Overwrite the original CSV
reranked_df.to_csv('roblox_top10_history.csv', index=False)
print(reranked_df)
print('Overwritten roblox_top10_history.csv') 