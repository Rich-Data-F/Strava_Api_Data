import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import Tuple
import ast
from data_processing import get_palmares

def create_activity_plots(filtered_df, user_firstname, user_lastname):
    fig, axs = plt.subplots(2, 2, figsize=(20, 20))
    plt.subplots_adjust(hspace=0.4)
    # Plot 1: All activities
    sns.scatterplot(data=filtered_df, x='distance', y='moving_time', ax=axs[0, 0])
    
    # Identify user activities
    user_activities = filtered_df[
        (filtered_df['firstname'] == user_firstname) & 
        (filtered_df['lastname'] == user_lastname) #['lastname'].str[0]
    ]
    
    if not user_activities.empty:
        axs[0, 0].scatter(user_activities['distance'], user_activities['moving_time'], color='red', marker='*', s=500, label='Your activities')
    
    axs[0, 0].set_title('All Activities')
    axs[0, 0].set_xlabel('Distance (km)')
    axs[0, 0].set_ylabel('Moving Time (hours)')
    axs[0, 0].legend('')

    # Plot 2-4: Activities by sport type
    sport_types = filtered_df['sport_type'].unique()
    for i, sport in enumerate(sport_types[:3]):
        row, col = divmod(i + 1, 2)
        sport_df = filtered_df[filtered_df['sport_type'] == sport]
        sns.scatterplot(data=sport_df, x='distance', y='moving_time', ax=axs[row, col])
        if not user_activities.empty:
            user_sport_activities = user_activities[user_activities['sport_type'] == sport]
            axs[row, col].scatter(user_sport_activities['distance'], user_sport_activities['moving_time'], color='red', marker='*', s=100, label='Your activities')
        axs[row, col].set_title(f'{sport} Activities')
        axs[row, col].set_xlabel('Distance (km)')
        axs[row, col].set_ylabel('Moving Time (hours)')
        axs[row, col].legend()

    return fig

def display_summary_statistics(filtered_df: pd.DataFrame):
    st.subheader("Summary Statistics")
    st.write(filtered_df.groupby('sport_type').agg({
        'distance': ['sum', 'mean'],
        'moving_time': ['sum', 'mean'],
        'avg_speed': 'mean',
        'name': 'count'
    }).reset_index())

def display_palmares(filtered_df: pd.DataFrame):
    st.subheader("Halls of Fame")

    sport_categories = {
        "Running (Trail + Running)": ['Trail', 'Run'],
        "Cycling (Gravel, Road, Mountain Bike, Virtual)": ['Gravel Ride', 'Ride', 'MountainBikeRide', 'VirtualRide'],
        "Swimming": ['Swim']
    }

    metrics = {
        "Highest ascent": 'total_elevation_gain',
        "Highest cumulative moving time": 'moving_time',
        "Highest cumulative distance": 'distance',
        "Highest average moving speed": 'avg_speed'
    }

    for category, sports in sport_categories.items():
        st.write(f"**{category}**")
        for metric_name, metric in metrics.items():
            result = get_palmares(filtered_df, sports, metric)
            st.write(f"{metric_name}:", result)

    st.write("**All Activities**")
    st.write("Highest cumulative moving time:", get_palmares(filtered_df, filtered_df['sport_type'].unique(), 'moving_time'))
    st.write("Highest number of activities:", filtered_df.groupby(['firstname', 'lastname'])['name'].count().nlargest(1).reset_index())
    st.write("Highest average moving speed:", get_palmares(filtered_df, filtered_df['sport_type'].unique(), 'avg_speed'))
