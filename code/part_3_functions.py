import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

def get_album_tracks(album_name, cur, artist_name = None):
    if artist_name == None:
        cur.execute(f"SELECT * FROM albums_data WHERE album_name = '{album_name}';")
    else:
        cur.execute(f"SELECT * FROM albums_data WHERE artist_0 = '{artist_name}' AND album_name = '{album_name}';")
    return pd.DataFrame(cur.fetchall(), columns= [x[0] for x in cur.description])[['track_id']]

def get_track_features(track_id, cur):
    cur.execute(f"SELECT * FROM features_data WHERE id = '{track_id}'")
    df = pd.DataFrame(cur.fetchall(), columns= [x[0] for x in cur.description])
    cur.execute(f"SELECT track_name FROM albums_data WHERE track_id = '{track_id}'")
    row = cur.fetchone()
    if row is not None:
        df['track_name'] = row[0]
    else:
        df['track_name'] = "Unknown"
    return df

def get_album_features(album_name, cur, artist_name = None):
    album = get_album_tracks(album_name,cur,artist_name)
    album_features = get_track_features(get_track_features(album['track_id'].iloc[0],cur),cur)
    for id in album['track_id'].iloc[0:]:
        album_features = pd.concat([album_features , get_track_features(id,cur)], axis = 0)
    return album_features


def album_summary(album_name, cur, artist_name = None, features = None):
    fig, (ax1, ax2) = plt.subplots(1, 2,figsize = (10,10))
    if features is None:
        features_data = get_album_features(album_name, cur, artist_name)
        features_data.plot.barh(ax = ax1, x='track_name', y=['danceability','energy','speechiness','acousticness','instrumentalness','liveness','valence'],
                                width = 0.9)
        features_data.plot.barh(ax = ax2, x='track_name', y='loudness',
                            width = 0.8)
        ax2.tick_params(labelleft=False)
        plt.tight_layout()
        plt.show()
    else:
        return 0
