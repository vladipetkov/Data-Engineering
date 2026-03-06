import sqlite3
import pandas as pd

con = sqlite3.connect("../spotify_database.db")
cur = con.cursor()

"""
Which artists are considered to be one-hit wonders?
"""

min_track_pop = 75

query = f"""
    SELECT
        artist_data.name, 
        artist_data.artist_popularity AS a_pop,
        MAX(tracks_data.track_popularity) AS hit_pop,
        MAX(tracks_data.track_popularity) - artist_data.artist_popularity AS gap
    FROM artist_data
    JOIN albums_data ON artist_data.id = albums_data.artist_id
    JOIN tracks_data ON albums_data.track_id = tracks_data.id
    GROUP BY artist_data.id HAVING MAX(tracks_data.track_popularity) > ?
    ORDER BY gap DESC
    """

cur.execute(query, (min_track_pop,))

rows = cur.fetchall()

df = pd.DataFrame(rows, columns=[x[0] for x in cur.description])

print(df.head())

"""
ex. 7 Are collaborations more popular?
"""

query = """
    SELECT 
        CASE 
            WHEN artist_1 != '' THEN 'Collab'
            ELSE 'Solo'
        END AS collab_or_solo,
        ROUND(AVG(tracks_data.track_popularity), 2) AS avg_pop,
    FROM albums_data
    JOIN features_data ON albums_data.track_id = features_data.id
    JOIN tracks_data ON features_data.id = tracks_data.id
    GROUP BY collab_or_solo
    ORDER BY avg_pop DESC
"""

cur.execute(query)

rows = cur.fetchall()

df = pd.DataFrame(rows, columns=[x[0] for x in cur.description])

print(df.head())

con.close()
