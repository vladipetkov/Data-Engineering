import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import part_3_functions as func

con = sqlite3.connect("spotify_database.db")
cur = con.cursor()

func.album_summary('Jar Of Flies',cur)
"""
ex. 5 Are explicit tracks more popular?
"""
explicit_popularity = []
nonexplicit_popularity = []

cur.execute("select track_popularity from tracks_data where explicit = 'true';")
rows = cur.fetchall()

for row in rows:
    explicit_popularity.append(row[0])

cur.execute("select track_popularity from tracks_data where explicit = 'false';")
rows = cur.fetchall()

for row in rows:
    nonexplicit_popularity.append(row[0])

plt.boxplot([explicit_popularity, nonexplicit_popularity], tick_labels=["Explicit Content", "Non-Explicit Content"])
plt.ylabel("Popularity Score")
plt.title("Popularity of Explicit vs Non-Explicit Content")
plt.show()

"""
ex. 6 Which artists have the highest proportion of explicit tracks?
"""
query = "select ar.name, count(*) from artist_data ar join albums_data al on ar.id = al.artist_id join tracks_data t on al.track_id = t.id " \
"where t.explicit = 'true' group by ar.name order by count(*) desc limit 10;"

cur.execute(query)
top_10_explicit_artists = cur.fetchall()

print("artist             songs \n------------------------")
for artist in top_10_explicit_artists:
    print(f"{artist[0]:20} {artist[1]}")
