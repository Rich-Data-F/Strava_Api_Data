import streamlit as st
import datetime as dt
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import Tuple
import ast
from data_processing import *
from strava_api import *
from bokeh.models import ColumnDataSource, HoverTool, Legend
from bokeh.models import Legend, LegendItem
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.palettes import Spectral10, Turbo256
import colorcet as cc



def display_club_details(selected_club):
    # Define sport_types at the beginning of the function
    sport_types = {
        "Running (Trail + Running)": ['Trail', 'Run'],
        "Cycling (Gravel, Road, Mountain Bike, Virtual)": ['Gravel Ride', 'Ride', 'MountainBikeRide', 'VirtualRide'],
        "Swimming": ['Swim']
    }

    # Read the CSV file
    df = pd.read_csv('data/all_club_activities.csv')
    
    # Filter activities for the selected club
    club_activities = df[df['club_name'] == selected_club]
    
    if not club_activities.empty:
        st.subheader(f"Member Activities for {selected_club}")
        
        for sport_name, sport_activities in sport_types.items():
            st.subheader(f"{sport_name} Activities")
            
            # Filter activities for this sport type
            sport_df = club_activities[club_activities['sport_type'].isin(sport_activities)]
            
            if sport_df.empty:
                st.write(f"No {sport_name} activities found for this club.")
                continue
            
            # Aggregate data by athlete
            athlete_stats = sport_df.groupby(['firstname', 'lastname']).agg({
                'distance': 'sum',
                'moving_time': 'sum',
                'avg_speed': 'mean'
            }).reset_index()
            
            # Calculate number of activities
            activity_counts = sport_df.groupby(['firstname', 'lastname']).size().reset_index(name='activity_count')
            athlete_stats = athlete_stats.merge(activity_counts, on=['firstname', 'lastname'])
            
            # Sort by number of activities and get top 50
            top_50_athletes = athlete_stats.sort_values('activity_count', ascending=False).head(50)
            
            # Create a color palette for athletes
            num_athletes = len(top_50_athletes)
            color_palette = Turbo256[:num_athletes]
            top_50_athletes['color'] = color_palette
            
            # Now create the Bokeh figure
            p = figure(title=f"Top 50 {sport_name} Athletes", 
                       x_range=(0, top_50_athletes['activity_count'].max() * 1.1),
                       y_range=(0, top_50_athletes['avg_speed'].max() * 1.1),
                       width=800, height=600, toolbar_location="right")
            
            # Add bubbles

            source = ColumnDataSource(top_50_athletes)
            bubbles = p.circle(x='activity_count', y='avg_speed', size='moving_time', source=source, fill_alpha=0.6, color='color', line_color=None)
            # Customize the plot
            p.xaxis.axis_label = "Number of Activities"
            p.yaxis.axis_label = "Average Speed"
            p.title.text_font_size = '16pt'
            
            # Add hover tool
            hover = HoverTool(tooltips=[
                ("Name", "@firstname @lastname"),
                ("Activities", "@activity_count"),
                ("Avg Speed", "@avg_speed{0.2f}"),
                ("Total Distance", "@distance{0.2f} km"),
                ("Moving Time (hours)", "@moving_time{0.2f}")
            ])
            p.add_tools(hover)
            
            # Create legend items
            legend_items = [
                LegendItem(label=f"{row['firstname']} {row['lastname']} ({row['activity_count']} activities)", renderers=[bubbles])
                for _, row in top_50_athletes.iterrows()
]
            # Add legend to the plot
            legend = Legend(items=legend_items, location="center_right", click_policy="hide")
            p.add_layout(legend, 'right')
            
            # Show the plot in Streamlit
            st.bokeh_chart(p)
            
            # Display a table with the data for reference
            st.dataframe(top_50_athletes[[
                'firstname', 'lastname', 'activity_count', 'avg_speed', 'distance', 'moving_time'
            ]], hide_index=True)
    else:
        st.warning(f"No activities found for {selected_club}.")

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


