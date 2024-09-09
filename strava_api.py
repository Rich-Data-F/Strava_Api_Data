import datetime as dt
import requests
import streamlit as st
from typing import Dict, Any, List, Optional

@st.cache_data(ttl=3600)
def get_athlete_info(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    athlete_url = 'https://www.strava.com/api/v3/athlete'
    response = requests.get(athlete_url, headers=headers)
    if response.status_code == 200:
        athlete_data = response.json()
        user_firstname = athlete_data['firstname']
        user_lastname = athlete_data['lastname']
        return athlete_data['firstname'], athlete_data['lastname']
    else:
        st.error(f"Failed to fetch athlete info. Status code: {response.status_code}")
        return None, None

@st.cache_data(ttl=3600)
def create_strava_auth_url(client_id: str, redirect_uri: str) -> str:
    scope = 'read,profile:read_all,activity:read_all'
    return f"https://www.strava.com/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}"

def exchange_code_for_token(client_id: str, client_secret: str, code: str) -> Dict[str, Any]:
    token_url = 'https://www.strava.com/oauth/token'
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'grant_type': 'authorization_code'
    }
    try:
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Failed to exchange code for token: {str(e)}")
        return {}

@st.cache_data(ttl=3600)
def get_athlete_stats(access_token: str) -> Dict[str, Any]:
    headers = {'Authorization': f'Bearer {access_token}'}
    athlete_url = 'https://www.strava.com/api/v3/athlete'
    stats_url = 'https://www.strava.com/api/v3/athletes/{}/stats'
  
    try:
        athlete_response = requests.get(athlete_url, headers=headers)
        athlete_response.raise_for_status()
        athlete_id = athlete_response.json()['id']
        stats_response = requests.get(stats_url.format(athlete_id), headers=headers)
        stats_response.raise_for_status()
        return stats_response.json()
    except requests.RequestException as e:
        st.error(f"Failed to fetch athlete stats: {str(e)}")
        return {}

@st.cache_data(ttl=3600)
def get_friend_activities(access_token: str) -> List[Dict[str, Any]]:
    # Implementation remains the same, add error handling
    headers = {'Authorization': f'Bearer {access_token}'}
    six_months_ago = int((dt.datetime.now() - dt.timedelta(days=180)).timestamp())
    activities_url = f'https://www.strava.com/api/v3/activities/following?after={six_months_ago}'
    response = requests.get(activities_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch friend activities. Status code: {response.status_code}")
#        st.write("Response content:", response.text)
        return []


@st.cache_data(ttl=3600)
def get_athlete_clubs(access_token: str) -> List[Dict[str, Any]]:
    headers = {'Authorization': f'Bearer {access_token}'}
    clubs_url = 'https://www.strava.com/api/v3/athlete/clubs'
    response = requests.get(clubs_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch clubs. Status code: {response.status_code}")
        return None

@st.cache_data(ttl=3600)
def get_club_members(access_token, club_id):
    headers = {'Authorization': f'Bearer {access_token}', 'accept': 'application/json'}
    members_url = f'https://www.strava.com/api/v3/clubs/{club_id}/members'
    response = requests.get(members_url, headers=headers)
    if response.status_code == 200:
        members = response.json()
        # Ensure each member has the expected fields
        for member in members:
            member['firstname'] = member.get('firstname', 'N/A')
            member['lastname'] = member.get('lastname', 'N/A')
            member['id'] = member.get('id', 'N/A')
        return members
    else:
        st.error(f"Failed to fetch club members. Status code: {response.status_code}")
        st.write("Response content:", response.text)
        return None
   
@st.cache_data(ttl=3600)
def get_club_activities(access_token: str, club_id: int, club_name: str) -> List[Dict[str, Any]]:
    headers = {'Authorization': f'Bearer {access_token}', 'accept': 'application/json'}
    activities_url = f'https://www.strava.com/api/v3/clubs/{club_id}/activities?page=1&per_page=200'
    response = requests.get(activities_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch club activities. Status code: {response.status_code}")
        st.write("Response content:", response.text)
        return None
