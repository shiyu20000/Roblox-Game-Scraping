import streamlit as st
import pandas as pd

st.set_page_config(page_title="Roblox Top Games Daily Stats", layout="wide")
st.title("Roblox Top Games Daily Stats")

@st.cache_data
def load_data():
    return pd.read_csv("roblox_top10_history.csv")

# Add a refresh button
if st.button("Refresh Data"):
    st.cache_data.clear()
    st.experimental_rerun()

df = load_data()
print(df.head())
print(df.columns)

if df.empty:
    st.warning("No data available. Run the scraper to collect data.")
else:
    st.dataframe(df)
    st.markdown("---")
    games = df['name'].unique()
    selected_games = st.multiselect("Select games to visualize:", games, default=list(games))
    filtered = df[df['name'].isin(selected_games)]
    if not filtered.empty:
        st.subheader("Concurrent Users Over Time")
        for game in selected_games:
            game_df = filtered[filtered['name'] == game]
            st.line_chart(game_df.set_index('date')['average_ccu'], height=200)
        st.subheader("Average Session Time Over Time")
        for game in selected_games:
            game_df = filtered[filtered['name'] == game]
            st.line_chart(game_df.set_index('date')['session_length'], height=200)
        st.subheader("Visits (Incremental) Over Time")
        for game in selected_games:
            game_df = filtered[filtered['name'] == game]
            # Ensure visits is numeric for plotting
            game_df = game_df.copy()
            game_df['visits'] = pd.to_numeric(game_df['visits'], errors='coerce')
            st.line_chart(game_df.set_index('date')['visits'], height=200)
        st.markdown("**Note:** The 'visits' column now represents incremental (daily) visits, not cumulative visits.") 
