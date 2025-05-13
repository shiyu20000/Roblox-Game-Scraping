import streamlit as st
import pandas as pd

st.set_page_config(page_title="Roblox Top Games Daily Stats", layout="wide")
st.title("Roblox Top Games Daily Stats")

@st.cache_data
def load_data():
    df = pd.read_csv("roblox_top10_history.csv")
    # Ensure correct types
    df['date'] = pd.to_datetime(df['date'])
    df['ranking'] = pd.to_numeric(df['ranking'], errors='coerce')
    df['visits'] = pd.to_numeric(df['visits'], errors='coerce')
    df['average_ccu'] = pd.to_numeric(df['average_ccu'], errors='coerce')
    df['session_length'] = pd.to_numeric(df['session_length'], errors='coerce')
    return df

# Add a refresh button
if st.button("Refresh Data"):
    st.cache_data.clear()
    st.experimental_rerun()

df = load_data()

if df.empty:
    st.warning("No data available. Run the scraper to collect data.")
else:
    st.dataframe(df)
    st.markdown("---")
    games = df['name'].unique()
    selected_games = st.multiselect("Select games to visualize:", games, default=list(games))
    filtered = df[df['name'].isin(selected_games)]
    if not filtered.empty:
        st.subheader("Average Concurrent Users (CCU) Over Time")
        for game in selected_games:
            game_df = filtered[filtered['name'] == game]
            st.line_chart(game_df.set_index('date')['average_ccu'], height=200)
        st.subheader("Average Session Length Over Time")
        for game in selected_games:
            game_df = filtered[filtered['name'] == game]
            st.line_chart(game_df.set_index('date')['session_length'], height=200)
        st.subheader("Visits (Daily) Over Time")
        for game in selected_games:
            game_df = filtered[filtered['name'] == game]
            st.line_chart(game_df.set_index('date')['visits'], height=200)
        st.markdown("**Note:** The 'visits' column represents daily visits.") 
