import streamlit as st
import pandas as pd

st.set_page_config(page_title="Roblox Top Games Daily Stats", layout="wide")
st.title("Roblox Top Games Daily Stats")

tab1, tab2 = st.tabs(["Top Game Data", "User Sentiment"])

with tab1:
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
        
        # Add combined top 10 visualization
        with st.expander("Combined Top 10 Games Daily Stats", expanded=True):
            # Get the latest date's top 10 games
            latest_date = df['date'].max()
            latest_top10 = df[df['date'] == latest_date].sort_values('ranking')['name'].tolist()
            
            # Filter data for these games
            top10_df = df[df['name'].isin(latest_top10)]
            
            # Create a pivot table for CCU
            ccu_pivot = top10_df.pivot_table(
                index='date',
                columns='name',
                values='average_ccu',
                aggfunc='sum'
            ).fillna(0)
            
            # Create a pivot table for visits
            visits_pivot = top10_df.pivot_table(
                index='date',
                columns='name',
                values='visits',
                aggfunc='sum'
            ).fillna(0)
            
            # Plot combined CCU
            st.markdown("### Combined Daily CCU for Top 10 Games")
            st.line_chart(ccu_pivot, height=300)
            
            # Plot combined visits
            st.markdown("### Combined Daily Visits for Top 10 Games")
            st.line_chart(visits_pivot, height=300)
            
            # Add summary statistics
            st.markdown("### Daily Summary Statistics")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total CCU (Latest Day)", f"{ccu_pivot.iloc[-1].sum():,.0f}")
                st.metric("Average CCU (Latest Day)", f"{ccu_pivot.iloc[-1].mean():,.0f}")
            with col2:
                st.metric("Total Visits (Latest Day)", f"{visits_pivot.iloc[-1].sum():,.0f}")
                st.metric("Average Visits (Latest Day)", f"{visits_pivot.iloc[-1].mean():,.0f}")
        
        st.markdown("---")
        games = df['name'].unique()
        selected_games = st.multiselect("Select games to visualize:", games, default=list(games))
        filtered = df[df['name'].isin(selected_games)]
        if not filtered.empty:
            with st.expander("Average Concurrent Users (CCU) Over Time", expanded=False):
                for game in selected_games:
                    game_df = filtered[filtered['name'] == game]
                    st.markdown(f"#### Concurrent Users for {game}")
                    st.line_chart(game_df.set_index('date')['average_ccu'], height=200)
            with st.expander("Average Session Length Over Time", expanded=False):
                for game in selected_games:
                    game_df = filtered[filtered['name'] == game]
                    st.markdown(f"#### Session Length for {game}")
                    st.line_chart(game_df.set_index('date')['session_length'], height=200)
            with st.expander("Visits (Daily) Over Time", expanded=False):
                for game in selected_games:
                    game_df = filtered[filtered['name'] == game]
                    st.markdown(f"#### Visits for {game}")
                    st.line_chart(game_df.set_index('date')['visits'], height=200)
            st.markdown("**Note:** The 'visits' column represents daily visits.")

with tab2:
    st.header("User Sentiment")
    # Load and show Discord activities
    try:
        discord_df = pd.read_csv("Roblox_discord_activities.csv")
        st.subheader("Discord Activities")
        st.dataframe(discord_df)
    except Exception as e:
        st.warning(f"Could not load Roblox_discord_activities.csv: {e}")

    # Load and show Streamer stats
    try:
        streamer_df = pd.read_csv("streamer_stats.csv")
        st.subheader("Streamer Stats")
        st.dataframe(streamer_df)
    except Exception as e:
        st.warning(f"Could not load streamer_stats.csv: {e}")

    # Load and show YouTube results
    try:
        yt_df = pd.read_csv("youtube_results.csv")
        st.subheader("YouTube Results")
        st.dataframe(yt_df)
    except Exception as e:
        st.warning(f"Could not load youtube_results.csv: {e}") 
