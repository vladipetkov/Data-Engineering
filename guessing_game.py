import part_3_functions as func
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3

def pick_3_songs_from_album(album_name,cur, artist_name = None):
    return func.get_album_tracks(album_name, cur, artist_name).sample(3).reset_index(drop=True)

def get_features_of_tracks(track_ids,cur):
    album_features = func.get_track_features(func.get_track_features(track_ids['track_id'].iloc[0],cur),cur)
    for id in track_ids['track_id'].iloc[0:]:
        album_features = pd.concat([album_features , func.get_track_features(id,cur)], axis = 0)
    return album_features

def show_features(features_of_tracks):
    fig, (ax1, ax2) = plt.subplots(1, 2,figsize = (10,10))
    features_of_tracks.plot.barh(ax = ax1, x='track_name', y=['danceability','energy','speechiness','acousticness','instrumentalness','liveness','valence'],
                            width = 0.9)
    ax1.invert_yaxis()
    ax1.set_yticklabels([1,2,3])
    features_of_tracks.plot.barh(ax = ax2, x='track_name', y='loudness',
                            width = 0.8)
    ax2.tick_params(labelleft=False)
    ax2.invert_yaxis()
    plt.tight_layout()
    plt.show()

def start_game(album_name,cur, artist_name = None):
    sampled_tracks = pick_3_songs_from_album(album_name,cur, artist_name = None)
    shuffled_tracks = sampled_tracks.sample(3).reset_index()
    shuffled_features = get_features_of_tracks(shuffled_tracks,cur)

    print("The three tracks are:\n", shuffled_features[['track_name']],'\nPlease enter the order which you think matches the graphs\n(for example 231 if:\n - the second song should be first\n - the third song be second\n - the first song be last)')
    print(shuffled_tracks)
    print(sampled_tracks)
    show_features(shuffled_features)
    solution = input("Please enter your solution as a permutation of 123 (231, 312 etc.): ")
    solution = [int(d)-1 for d in str(solution)]
    #print(solution)
    
    ok=0
    if(solution[0] == shuffled_tracks['index'].iloc[0]):
        print("The first one is correct")
        ok = 1
    if(solution[1] == shuffled_tracks['index'].iloc[1]):
        print("The second one is correct")
        ok = 1
    if(solution[2] == shuffled_tracks['index'].iloc[2]):
        print("The third one is correct")
        ok = 1
    if ok == 0: print("None of them are correct")

    print('The correct order was: \n',get_features_of_tracks(sampled_tracks,cur)[['track_name']])



con = sqlite3.connect("spotify_database.db")
cur = con.cursor()

print("How to play:\nPick an album you are familiar with. We will randomly sample 3 songs from that album and show you the features (danceability, acousticness, energy etc) after which you have to match the songs to their features.")
picked_album = input("Please enter the name of the album (Watch out for capitalization): ")
ok = input("Do you want to provide an artist name? (Y/N): ")
if ok == 'N':
    picked_name = None
else: picked_name = input("Enter the name of the artist: ")

start_game(picked_album,cur,picked_name)