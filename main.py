import pandas as pd
import datetime as dt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from cryptography.fernet import Fernet
from strava_api import *
from data_processing import *
from visualization import *
import streamlit as st
import requests
import matplotlib.pyplot as plt
import seaborn as sns
import json

# Load environment variables and decrypt secrets
load_dotenv()
CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
REDIRECT_URI = os.getenv("STRAVA_REDIRECT_URI", "http://localhost:8501")
encryption_key = os.getenv("ENCRYPTION_KEY").encode()
cipher_suite = Fernet(encryption_key)
CLIENT_SECRET = cipher_suite.decrypt(os.getenv("STRAVA_CLIENT_SECRET").encode()).decode()

# Add this function to check the last fetch time
def save_last_selected_club(club_name):
    with open('last_selected_club.json', 'w') as f:
        json.dump({'last_club': club_name}, f)

def load_existing_activities():
    file_path = 'data/all_club_activities.csv'
    try:
        return pd.read_csv(file_path, parse_dates=['upload_date'])
        #pd.read_csv(file_path, parse_dates=['upload_date'])
    except FileNotFoundError:
        return pd.DataFrame()

def load_last_selected_club():
    try:
        with open('data/last_selected_club.json', 'r') as f:
            data = json.load(f)
        return data.get('last_club')
    except FileNotFoundError:
        return None

def get_last_fetch_time(club_id):
    try:
        with open('data/fetch_log.json', 'r') as f:
            log = json.load(f)
        return datetime.fromisoformat(log.get(str(club_id), '2000-01-01T00:00:00'))
    except (FileNotFoundError, json.JSONDecodeError):
        return datetime.fromisoformat('2000-01-01T00:00:00')

# Add this function to update the fetch log
def update_fetch_log(club_id):
    try:
        with open('data/fetch_log.json', 'r') as f:
            log = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        log = {}
    
    log[str(club_id)] = datetime.now().isoformat()
    
    with open('data/fetch_log.json', 'w') as f:
        json.dump(log, f)

def display_athlete_stats():
    stats = get_athlete_stats(st.session_state.access_token)
    st.subheader("Your Activity Stats")
    stats_df = pd.DataFrame({
        'Metric': ['Total Distance (km)', 'Total Elevation Gain (m)', 'Total Activities'],
        'All Time': [stats['all_ride_totals']['distance']/1000, stats['all_ride_totals']['elevation_gain'], stats['all_ride_totals']['count']],
        'Last 4 Weeks': [stats['recent_ride_totals']['distance']/1000, stats['recent_ride_totals']['elevation_gain'], stats['recent_ride_totals']['count']]
    })
    st.table(stats_df)

def display_friend_activities():
    st.subheader("Your Followed Friends Stats")
    friend_activities = get_friend_activities(st.session_state.access_token)
    if isinstance(friend_activities, list):
        # Process and display friend activities
        # (This part can be expanded based on your specific requirements)
        pass
    else:
        st.error("Failed to retrieve friend activities.")

def display_clubs():
    st.subheader("Clubs you belong to")
    clubs = get_athlete_clubs(st.session_state.access_token)
    if clubs:
        st.session_state.clubs_df = pd.DataFrame(clubs)
        st.dataframe(st.session_state.clubs_df[['id', 'name', 'sport_type']])
    else:
        st.warning("No clubs found or unable to retrieve them.")

def display_club_details(selected_club):
    club_id = st.session_state.clubs_df[st.session_state.clubs_df['name'] == selected_club]['id'].values[0]
    members = get_club_members(st.session_state.access_token, club_id)
    if members:
        st.subheader(f"Members of {selected_club}")
        members_df = pd.DataFrame(members)
        st.dataframe(members_df[['firstname', 'lastname', 'id']])
    else:
        st.warning("Unable to retrieve club members.")

def display_club_stats(selected_club, all_activities_df):
    st.subheader(f"Stats for {selected_club}")
    club_activities = all_activities_df[all_activities_df['club_name'] == selected_club]
    if not club_activities.empty:
        st.write(f"Total activities: {len(club_activities)}")
        st.write(f"Total distance: {club_activities['distance'].sum():.2f} km")
        st.write(f"Total moving time: {club_activities['moving_time'].sum():.2f} hours")
    else:
        st.write("No activities found for this club.")

def display_club_activities(selected_club, clubs_df):
    get_athlete_info(st.session_state.access_token)
    selected_club_id = clubs_df[clubs_df['name'] == selected_club]['id'].values[0]
    # Load existing activities
    all_activities_df = pd.read_csv('data/all_club_activities.csv', parse_dates=['upload_date'])
    if 'club_id' not in all_activities_df.columns:
        st.warning("No club activities found. Please fetch activities first.")
        return
    # Filter activities for the selected club
    df = all_activities_df[all_activities_df['club_id'] == selected_club_id].copy()
    if df.empty:
        st.warning("No activities found for this club. Please fetch activities first.")
        return
    st.write(f"Showing details for {selected_club}. Total activities: {len(df)}")
    # Get min and max dates
    min_date = df['upload_date'].min().date()
    max_date = df['upload_date'].max().date()
    # Ensure min_date and max_date are different
    if min_date == max_date:
        min_date = min_date - timedelta(days=1)
        max_date = max_date + timedelta(days=1)
    # Create the slider
    # Calculate a default range (e.g., last 30 days)
    default_end = max_date
    default_start = max(min_date, default_end - timedelta(days=30))
    date_range = st.slider(
        "Select date range",
        min_value=min_date,
        max_value=max_date,
        value=(default_start, default_end),
        format="YYYY-MM-DD"
    )
    # Filter data based on selected date range
    mask = (df['upload_date'].dt.date >= date_range[0]) & (df['upload_date'].dt.date <= date_range[1])
    filtered_df = df.loc[mask]
    # Get user information
    #    user_firstname = st.text_input("Enter your first name")
    #    user_lastname_initial = st.text_input("Enter your last name initial")'''
    # Create and display plot
    athlete_firstname, athlete_lastname = get_athlete_info(st.session_state.access_token)
    if athlete_firstname and athlete_lastname:
        fig = create_activity_plots(filtered_df, athlete_firstname, athlete_lastname)  # Using first letter of lastname
        st.pyplot(fig)
        # Display statistics and palmares
        display_summary_statistics(filtered_df)
    else:
        st.error("Failed to retrieve athlete information.")

def main():
    st.title('Strava Data Analysis')
    if 'access_token' not in st.session_state:
        st.session_state.access_token = None
    if 'selected_club' not in st.session_state:
        st.session_state.selected_club = load_last_selected_club()
    if 'code' in st.query_params:
        code = st.query_params['code']
        token_response = exchange_code_for_token(CLIENT_ID, CLIENT_SECRET, code)
        if 'access_token' in token_response:
            st.session_state.access_token = token_response['access_token']
            st.success("Successfully authorized!")
        else:
            st.error(f"Failed to obtain access token. Error: {token_response.get('error', 'Unknown error')}")
        del st.query_params['code']
    if st.session_state.access_token:
        display_athlete_stats()
        display_friend_activities()
        display_clubs()
         # Get athlete info
        get_athlete_info(st.session_state.access_token) # get_athlete_info(st.session_state.access_token)
        # Load existing activities
        #all_activities_df = load_existing_activities()
        all_activities_df = pd.read_csv('data/all_club_activities.csv', parse_dates=['upload_date'])
        
        # Add a button to trigger fetching
        if st.button('Fetch New Activities'):
        # Fetch and consolidate activities for all clubs
            all_activities_df = pd.DataFrame()
            clubs = get_athlete_clubs(st.session_state.access_token)
            if clubs:
                for club in clubs:
                    club_id = club['id']
                    club_name = club['name']
                    # Check if club has more than 500 members
                    members = get_club_members(st.session_state.access_token, club_id)
                    if len(members) > 300:
                        st.warning(f"Skipping {club_name} as it has more than 300 members.")
                        continue
                    # Check if last fetch was more than 24 hours ago
                    last_fetch_time = get_last_fetch_time(club_id)
    #                if datetime.now() - last_fetch_time < timedelta(hours=24):
    #                   st.info(f"Skipping {club_name} as it was fetched less than 24 hours ago.")
    #                    continue
                    new_activities_json = get_club_activities(st.session_state.access_token, club_id, club_name)
                    if new_activities_json:
                        new_activities_df = process_activities(new_activities_json, club_id, club_name)
                        all_activities_df = pd.concat([all_activities_df, new_activities_df])
                        # Update the register after each successful fetch
                        all_activities_df = update_activities_register(all_activities_df)
                        update_fetch_log(club_id)  # Update the fetch log
                        st.success(f"Retrieved activities for {club_name}")
                    else:
                        st.warning(f"Failed to retrieve activities for {club_name}. Stopping further fetches.")
                        break  # Stop fetching on first error (e.g., 503)
                st.success(f"Total unique activities: {len(all_activities_df)}")

        # Create a dropdown for club selection
        club_names = st.session_state.clubs_df['name'].tolist()
        default_index = club_names.index(st.session_state.selected_club) if st.session_state.selected_club in club_names else 0
        # selected_club = st.selectbox("Select a club for detailed view", club_names, index=default_index)
        selected_club = st.selectbox("Select a club for detailed view", st.session_state.clubs_df['name'])
        # club_names, index=default_index) 
        if selected_club:
            st.session_state.selected_club = selected_club
            save_last_selected_club(selected_club)
            display_club_details(selected_club)
            display_club_activities(selected_club, st.session_state.clubs_df)
            # Display stats for the selected club using existing data
            display_club_stats(selected_club, all_activities_df)
                    # Button to display palmares
        if st.button('Display Palmares'):
            club_activities = all_activities_df[all_activities_df['club_name'] == selected_club]
            display_palmares(club_activities)
#            display_palmares(filtered_df)
    else:
        st.write("Click the button below to authorize this app to access your Strava data.")
        if st.button('Authorize Strava Access'):
            auth_url = create_strava_auth_url(CLIENT_ID, REDIRECT_URI)
            st.markdown(f"[Click here to authorize]({auth_url})", unsafe_allow_html=True)

if __name__ == "__main__":
    main()