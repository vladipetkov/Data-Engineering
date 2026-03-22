# Data Engineering Project
This repository contains a dashboard for a spotify database and some additional code for general data insight and wrangling techniques.

## Homework Parts folder
- part_1.py provides a short analysis of the linear relationship between artist followers and popularit and an analysis of the distribution of genres
- part_3.py (partially uses part_3_functions.py)
    - makes an analysis of an albums features
    - evaluates relationship between track popularity and explicitness
    - code for converting very speciffic genres into broader genres
- part_4.py evaluates the average features of the songs by decade


# Spotify Dashboard

# Sidebar features
The sidebar acts as an easy to navigate menu for switching between looking something up, to the main statistics, to the business tab
- Genre Filtering: Toggle filtering on/off and select specific genres to update the dashboard
- Lookup: type in an Artist, Album or Track to learn more
- Business Tab: Navigates to the Festival tab

# Main page
This page contains an overview of various statistics relating to genre trends, top artists and number of releases
- Main Statistics: total artists, average followers, average artist popularity, and average track popularity
- Top data tables: to view most popular/followed artists and most popular albums (such as "1989" by Taylor Swift)
- Album Releases Heatmap: shows album release concentration across time
- Album releases by month in 2023
- Genre distribution (pie chart)
- Song duration by decade (boxplot)
- Genre popularity over time (line graph)

# Lookup
## Artist Lookup
- Search: search for any artist by name and choose from a grid of artists
- Profile: view the artists global ranking, total followers, primary genres and the popularity score of their most recent album
- Discography performance: a table of albums and compilations, and track the artists release popularity over time (line chart)
- Averages: see the artists total number of releases, average album length, and average popularity score
- Track Analysis: a ranked list of the artists individual tracks, their overall track count and average song length
- Audio Profile: compare the acoustic profiles (danceability, energy, valence etc.) of the artists top three tracks using a dedicated chart

## Album Lookup
- Search: use input fields to search for albums, artists, or individual tracks to pull up relevant data
- Overview: view album cover art, release date, label, and its global popularity ranking
- Comparative metrics: compare the albums overall popularity, total duration, and track count against the artists historical averages
- Album Features: a line chart of the albums average audio features (danceability, energy, valence etc.) and key, loudness, and tempo metrics
- Tracklist and Leaderboard: A chronological tracklist next to a leaderboard ranking the songs by popularity

## Track Lookup
- Track Analysis: view global ranking, length, and featured artists
- Track Feature Comparison: select multiple tracks from an album to graph and compare their profiles

# Festival Optimizer
## How to Use:
Use the sidebar to select the number of stages, number of festival days and what genres and budget should each stage have.
Click "Run Optimization" to calculate a potential festival lineup and view its statistics.

## Key Features
- Main Results: Total Cost, Total Appeal, Number of artists
- Stage metrics: Budget summaries, Appeal chart, Genre Distribution, participating artists relevance (song release dates)
- Worst-Best comparison: you can compare the best solutions metrics to the worst
- Lineup: The algorythm provides the optimal lineup for maximising appeal



## Requirements: 
streamlit, requests, sqlite3, db, pandas, difflib, calendar, base64, pathlib, plotly, io, pulp

Disclaimer: The dashboard Festival Page uses a stylized version (with AI). The original is still present under the "original festival optimization files" folder.