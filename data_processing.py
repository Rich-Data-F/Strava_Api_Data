import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
import ast
import requests

def process_activities(activities: List[Dict], club_id: int, club_name: str) -> pd.DataFrame:
    if not activities:
        return pd.DataFrame()
    df = pd.DataFrame(activities)
    df['distance'] = round(df['distance'] / 1000, 2)  # Convert to kilometers rounded to 2 decimals
    df['moving_time'] = round(df['moving_time'] / 3600, 2)  # Convert to hours rounded to 2 decimals
    df['club_id'] = club_id
    df['club_name'] = club_name
    df['upload_date'] = datetime.now()
    if 'distance' in df.columns and 'moving_time' in df.columns:
        df['avg_speed'] = round(df['distance'] / df['moving_time'], 2)
    else:
        print("Warning: Unable to calculate average speed due to missing data")
    # Drop the original athlete column and the temporary athlete_dict column
    # Extract firstname and lastname from the athlete dictionary
    df['athlete_dict'] = df['athlete'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
    df['firstname'] = df['athlete_dict'].apply(lambda x: x.get('firstname', 'N/A'))
    df['lastname'] = df['athlete_dict'].apply(lambda x: x.get('lastname', 'N/A'))
    df = df.drop(columns=['athlete', 'athlete_dict'])    
    return df

def update_activities_register(new_activities_df: pd.DataFrame) -> pd.DataFrame:
    """
    Update the activities register with new activities.
    
    Args:
        new_activities_df (pd.DataFrame): DataFrame containing new activities
    
    Returns:
        pd.DataFrame: Updated DataFrame with all activities
    """
    file_path = 'data/all_club_activities.csv'
    
    try:
        existing_df = pd.read_csv(file_path, parse_dates=['upload_date'])
        combined_df = pd.concat([existing_df, new_activities_df])
        combined_df = combined_df.sort_values('upload_date').drop_duplicates(
            subset=['name', 'moving_time', 'club_id'], keep='last'
        )
        combined_df = combined_df.sort_values('upload_date', ascending=False).reset_index(drop=True)
    except FileNotFoundError:
        combined_df = new_activities_df
    
    combined_df.to_csv(file_path, index=False)
    return combined_df

def get_palmares(df: pd.DataFrame, sport_types: List[str], metric: str) -> pd.DataFrame:
    return df[df['sport_type'].isin(sport_types)].groupby(['firstname', 'lastname'])[metric].max().nlargest(3).reset_index()
