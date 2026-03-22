# Data Engineering
# mainpage
-Genre keywords
All genres grouped under 'main' genres. These main genres are selectable in the genre filter in the sidebar. The selection is then run through the where_selected_genres to make a reusable where clause.


functions:
-where_selected_genres
takes the list of genre keywords from the genre filter and returns a where clause that can be used in all sql queries in the rest of the code, using {where} in the query and a list of parameters for the query.

-get_kpis
Uses queries to get dashboard statistics: Total number of artists, Average followers, Average artist popularity, Average track popularity.

-top_artists_popularity, followers, album popularity
Returns dataframe with top 100 statistics.

-heatmap
Uses data to retrieve all releases in 2023. This is then later counted per day and entered into a seaborn heatmap.

-track_duration
Retrieves track duration grouped by decade. Then stored in a dataframe to use for a boxplot comparison.

-get_genre_popularity
Filters by selected years, takes average track popularity per year and groupes into broad genres for plotting.
