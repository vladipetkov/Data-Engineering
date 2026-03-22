import streamlit as st
import requests
import sqlite3
from db import get_connection
import pandas as pd
from difflib import SequenceMatcher
import calendar
from pathlib import Path

logo_path = Path(__file__).parent.parent / "supporting" / "logo.png"
st.set_page_config(page_title="Album Lookup", layout="wide")
st.logo("supporting/logo.png", size = "large")

with st.sidebar:
    selectbox_option = st.sidebar.selectbox(
    "Looking for something specific?",
    ("Look up an Artist", "Look up an Album or a Track"),
    index = None,
    placeholder="Look up..."
    )
    
    artist_page_path = Path(__file__).parent / "1_artist_page.py"
    album_page_path = Path(__file__).parent / "2_album_page.py"
    if selectbox_option == "Look up an Artist":
        st.switch_page("pages/1_artist_page.py")
    elif selectbox_option == "Look up an Album or a Track":
        st.switch_page("pages/2_album_page.py")

    st.space(500)
    
    event_planning_path = Path(__file__).parent / "4_event_planning.py"
    if st.sidebar.button("Business Tab" , type = "primary", width = "stretch"):
        st.session_state["play_event_planning_intro"] = True
        st.switch_page("pages/4_event_planning.py")

conn = get_connection()
cursor = conn.cursor()

def similar_names_search(item, similarity_score):
    df = pd.read_sql_query("select distinct a.album_id, a.album_name, b.name from albums_data a join artist_data b on b.id = a.artist_id;", conn, index_col= ['album_id'])

    similar_albums = []

    for index, row in df.iterrows():
        if SequenceMatcher(None, item, row['album_name']).ratio() > similarity_score:
            similar_albums.append([index, row['album_name'], row['name']])
    return similar_albums

def return_latest_album_picture(album, artist):
    try:
        refined_name = f"{album}+{artist}".replace(" ", "+")
        url = f"https://itunes.apple.com/search?term={refined_name}&entity=album&limit=1"
        data = requests.get(url).json()

        if data["resultCount"] > 0:
            result = data["results"][0]
            cover = result["artworkUrl100"]
            return cover
        else:
            return "https://imageio.forbes.com/specials-images/imageserve/5ed6636cdd5d320006caf841/The-Blackout-Tuesday-movement-is-causing-Instagram-feeds-to-turn-black-/0x0.jpg?width=960&dpr=2"
    except Exception:
        return "https://imageio.forbes.com/specials-images/imageserve/5ed6636cdd5d320006caf841/The-Blackout-Tuesday-movement-is-causing-Instagram-feeds-to-turn-black-/0x0.jpg?width=960&dpr=2"


def search_similar_results(name):
    similar_names = similar_names_search(name, 0.65)

    if len(similar_names) == 0:
        st.warning("There are no results found.")
    else:
        display_search_results(similar_names)

def display_search_results(results, track_index):
    st.header("There are multiple outputs of the current search:")

    col0, col1, col2, col3 = st.columns(4)
    switch = 0
    for result in results:
        if track_index:
            button_key = result[3]
        else:
            button_key = result[0]

        if switch == 0:
            col0.image(return_latest_album_picture(result[1],result[2]).replace("100x100","350x350"))
            switch+=1
            button_text = f"{result[1]} by {result[2]}"
            if col0.button(label = button_text, key = button_key, width = 350):
                modify_state(result, track_index)
            col0.space("small")
        elif switch==1:
            col1.image(return_latest_album_picture(result[1],result[2]).replace("100x100","350x350"))
            switch+=1
            button_text = f"{result[1]} by {result[2]}"
            if col1.button(label = button_text, key = button_key, width = 350):
                modify_state(result, track_index)
            col1.space("small")
        elif switch==2:
            col2.image(return_latest_album_picture(result[1],result[2]).replace("100x100","350x350"))
            switch+=1
            button_text = f"{result[1]} by {result[2]}"
            if col2.button(label = button_text, key = button_key, width = 350):
                modify_state(result, track_index)
            col2.space("small")
        elif switch==3:
            col3.image(return_latest_album_picture(result[1],result[2]).replace("100x100","350x350"))
            switch=0
            button_text = f"{result[1]} by {result[2]}"
            if col3.button(label = button_text, key = button_key, width = 350):
                modify_state(result, track_index)
            col3.space("small")

def modify_state(result_list, track_index):

    if track_index:
        track_id = result_list[3]
    else:
        track_id = ""

    st.session_state.album_name = ""
    st.session_state.artist_name_album_search = ""
    st.session_state.track_name = ""
    st.session_state.album_id = result_list[0]
    st.session_state.track_id = track_id
    st.rerun()

def search_engine(album, artist, track):
    search_by_track_index = False

    data = [] #dummy initiation
    if track and album:
        search_by_track_index = True
        successful_search_track = False
        if artist:
            query = f"select a.album_id, a.album_name, b.name, a.track_id, track_name from albums_data a join artist_data b on a.artist_id = b.id where track_name like '%{track}%' collate nocase and album_name like '%{album}%' collate nocase and b.name like '%{artist}%' collate nocase group by album_id;"
            cursor.execute(query)
            data = cursor.fetchall()
            if data != None:
                successful_search_track = True

        if not successful_search_track:
            query = f"select a.album_id, a.album_name, b.name, a.track_id, track_name from albums_data a join artist_data b on a.artist_id = b.id where track_name like '%{track}%' collate nocase and album_name like '%{album}%' collate nocase group by album_id;"
            cursor.execute(query)
            data = cursor.fetchall()
    elif track:
        search_by_track_index = True
        successful_search_track = False
        if artist:
            query = f"select a.album_id, a.album_name, b.name, a.track_id, a.album_type from albums_data a join artist_data b on a.artist_id = b.id where track_name like '%{track}%' collate nocase and b.name like '%{artist}%' collate nocase group by album_id;"
            cursor.execute(query)
            data = cursor.fetchall()
            if data != None:
                successful_search_track = True

        if not successful_search_track:
            query = f"select a.album_id, a.album_name, b.name, a.track_id, a.album_type from albums_data a join artist_data b on a.artist_id = b.id where track_name like '%{track}%' collate nocase group by album_id;"
            cursor.execute(query)
            data = cursor.fetchall()
    elif album or artist:
        if album:
            successful_search_album = False
            if artist:
                query = f"select distinct a.album_id, a.album_name, b.name from albums_data a join artist_data b on a.artist_id = b.id where album_name like '%{album}%' collate nocase and b.name like '%{artist}%' collate nocase and album_type = 'album';"
                cursor.execute(query)
                data = cursor.fetchall()
                if data != None:
                    successful_search_album = True

            if not successful_search_album:
                query = f"select distinct a.album_id, a.album_name, b.name from albums_data a join artist_data b on a.artist_id = b.id where album_name like '%{album}%' collate nocase and album_type = 'album';"
                cursor.execute(query)
                data = cursor.fetchall()
        else:
            query = f"select distinct a.album_id, a.album_name, b.name from albums_data a join artist_data b on a.artist_id = b.id where b.name like '%{artist}%' collate nocase and album_type = 'album';"
            cursor.execute(query)
            data = cursor.fetchall()

    if len(data) == 0:
        # search_similar_results(album) implement if there is time left
        st.warning("There are no results found.")
    elif len(data) == 1:
        if search_by_track_index:
            display_data(data[0][0], data[0][3])
        else:
            display_data(data[0][0], None)
    else:
        display_search_results(data, search_by_track_index)

def display_data(album_id, track_id):

    albums_query = f"select distinct a.album_name, b.name, a.release_date, a.album_popularity, a.total_tracks, sum(a.duration_sec), a.label, a.track_id, b.id from albums_data a join artist_data b on b.id = a.artist_id where a.album_id = '{album_id}' group by album_id;"
    cursor.execute(albums_query)
    album_data = cursor.fetchone()

    def return_tracks_data(track_id_, is_track_number):
        if is_track_number:
            cursor.execute(f"select a.track_number, a.track_name, a.track_id, a.artist_0, a.artist_1, a.artist_2, a.artist_3, a.artist_4, a.artist_5, a.artist_6, c.key, c.loudness, c.tempo, a.duration_sec, a.artist_id from albums_data a join tracks_data b on a.track_id = b.id join features_data c on b.id = c.id  where album_id = '{album_id}' order by track_number asc limit 1;")
            return cursor.fetchone()
        else:
            cursor.execute(f"select a.track_number, a.track_name, a.track_id, a.artist_0, a.artist_1, a.artist_2, a.artist_3, a.artist_4, a.artist_5, a.artist_6, c.key, c.loudness, c.tempo, a.duration_sec, a.artist_id from albums_data a join tracks_data b on a.track_id = b.id join features_data c on b.id = c.id  where track_id = '{track_id_}' order by track_number asc;")
            return cursor.fetchone()
    
    def display_track(track_data):
        track_id = track_data[2]
        track_name = track_data[1]
        artist_id = track_data[14]

        average_features_extra_query = f"select avg(c.key), avg(c.loudness), avg(c.tempo) from albums_data a join tracks_data b on a.track_id = b.id join features_data c on b.id = c.id where artist_id = '{artist_id}';"
        cursor.execute(average_features_extra_query)
        average_features_extra = cursor.fetchone()

        col18, col19 = st.columns([1,2])
        with col18:
            st.space(4)
            st.image(return_latest_album_picture(album_data[1], album_data[0]).replace("100x100","400x400"))
            st.header("FEATURES")

            st.metric("Track Key", value = track_data[10], delta = f"{round(track_data[10]-average_features_extra[0], 1)} vs Average Artist Track" ,format = "localized", border = True )
            st.metric("Track Loudness", value = f"{round(track_data[11], 2)} Db", delta = f"{round(track_data[11]-average_features_extra[1], 1)} vs Average Artist Track" , format = "localized", border = True )
            st.metric("Track Tempo", value = f"{round(track_data[12], 1)} BPM ", delta = f"{round(track_data[12]-average_features_extra[2], 1)} vs Average Artist Track" , format = "localized", border = True )
        
        with col19:
            
            st.title(f"{track_name}", width = "stretch")
            st.text(f"by {track_data[3]}", width = "stretch")

            query = f"with sorted_track_popularity as (select ROW_NUMBER() OVER (ORDER BY track_popularity DESC) AS position, track_id, track_popularity from (select track_id, track_popularity from albums_data a join tracks_data b on track_id = b.id) t) select position from sorted_track_popularity where track_id = '{track_id}';"
            cursor.execute(query)
            popularity_rank = cursor.fetchone()

            if popularity_rank[0] <= 1000:
                st.badge(f"# {popularity_rank[0]} Popular Track in the World",color = "green")

            col20, col21 = st.columns(2)
            with col20:
                st.space(16)
                st.metric(f"Song Length", value = f"{int(track_data[13]//60)}min {int(track_data[13]%60)} sec", border = False )
            with col21:
                st.space(16)
                featured_artists = []
                for artist in track_data[3:10]:
                    if artist != "" and artist != track_data[3]:
                        featured_artists.append(artist)

                st.metric(label="This song features", value = f"{len(featured_artists)} Artist(s)", border= False)
                if len(featured_artists) > 0:
                    for artist in featured_artists:
                        st.subheader(performer[0])
        
            query = f"select a.track_name as 'Track Name', c.danceability as 'Danceability', c.energy as 'Energy', c.liveness as 'Liveness', c.valence as 'Valence', c.speechiness as 'Speechiness', c.acousticness as 'Acousticness', c.instrumentalness as 'Instrumentalness' from albums_data a join tracks_data b on a.track_id = b.id join features_data c on b.id = c.id where a.album_id = '{album_id}';"
            album_features_df = pd.read_sql_query(query, conn, index_col=['Track Name'])

            if len(featured_artists) > 0:
                st.space(135)
            else:
                st.space(200)

            selected_rows = st.multiselect(label = "Select Tracks on the Album", options = album_features_df.index, default = track_data[1])

            filtered_df = album_features_df.loc[selected_rows]
            st.line_chart(filtered_df.transpose())      

    if album_data[4] == 1:
        track_id = album_data[7] #update just in case

        track_data = return_tracks_data(track_id, False)
        display_track(track_data)
    else:
        #ALBUM
        col4, col5 = st.columns([1,2])
        with col4:
            st.space(4)
            st.image(return_latest_album_picture(album_data[1], album_data[0]).replace("100x100","400x400"))
        
        with col5:
            
            st.title(f"{album_data[0]}", width = "stretch")
            
            query = f"with sorted_album_popularity as (select ROW_NUMBER() OVER (ORDER BY album_popularity DESC) AS position, album_id, album_popularity from (select distinct album_id, album_popularity from albums_data) t) select position from sorted_album_popularity where album_id = '{album_id}';"
            cursor.execute(query)
            popularity_rank = cursor.fetchone()
            badge_index = False
            if popularity_rank[0] <= 500:
                badge_index = True

            col6, col7 = st.columns([5,4])
            with col6:
                st.text(f"by {album_data[1]}", width = "stretch")
                if badge_index:
                    st.badge(f"# {popularity_rank[0]} Popular Album in the World",color = "green")
                st.space(25)
                col6.metric(label = "Label", value = album_data[6])
            with col7:
                query = f"with sorted_album_popularity as (select ROW_NUMBER() OVER (ORDER BY album_popularity DESC) AS position, album_id, album_popularity from (select distinct album_id, album_popularity from albums_data where album_type = 'album') t) select position from sorted_album_popularity where album_id = '{album_id}';"
                cursor.execute(query)
                popularity_rank = cursor.fetchone()

                if badge_index:
                    st.space(25)

                st.space(60)
                raw_month = int(album_data[2][5:7])
                month = calendar.month_abbr[raw_month]
                col7.metric(label = "Released on", value = f"{album_data[2][8:10]} {month} {album_data[2][:4]}")
        cursor.execute("select avg(album_popularity), avg(total_duration), avg(total_tracks) from (select distinct album_id, album_popularity, sum(duration_sec) as total_duration, total_tracks from albums_data where album_type = 'album' group by album_id);")
        average_album_specs = cursor.fetchone()

        col8,col9, col10 = st.columns(3)
        with col8:
            st.metric(label = "Album Popularity", value=album_data[3], delta = f"{round(album_data[3]-average_album_specs[0], 1)} vs average", border = True)
        with col9:
            delta_time = album_data[5]-average_album_specs[1]
            st.metric(label = "Total Duration", value = f"{int(album_data[5]//60)}min {int(album_data[5]%60)}sec", delta = f"{int(delta_time//60)}min {int(delta_time%60)}sec vs average", border = True)
        with col10:
            st.metric(label = "Total Tracks", value = album_data[4], delta = f"{round(album_data[4] - average_album_specs[2])} vs average",border = True)

        query = f"with album_filtered as (select artist_0, artist_1, artist_2, artist_3, artist_4, artist_5, artist_6 from albums_data where album_id = '{album_id}') \
            select artists from (select artist_0 as artists from album_filtered union select artist_1 from album_filtered union select artist_2 from album_filtered union \
            select artist_3 from album_filtered union select artist_4 from album_filtered union select artist_5 from album_filtered union select artist_6 from album_filtered) \
            filter where artists != '' and artists != (select name from artist_data a join albums_data b on a.id = b.artist_id where artist_id = (select distinct artist_id from albums_data where album_id = '{album_id}'));"
        cursor.execute(query)
        performers = cursor.fetchall()

        col13, col14 = st.columns([1,2])
        with col13:
            st.header("This Album Includes")
            st.space(2)
            st.metric(label="in total", value = f"{len(performers)} Featured Artist(s)", border = True)
        with col14:  
            st.space(70)
            switch = 0
            col25, col26,col27 = st.columns(3)
            for performer in performers:
                if switch == 0:
                    with col25:
                        col25.subheader(performer[0])
                        switch+=1
                        col25.space(1)
                        continue
                if switch == 1:
                    with col26:
                        col26.subheader(performer[0])
                        switch+=1
                        col26.space(1)
                        continue
                if switch == 2:
                    with col27:
                        col27.subheader(performer[0])
                        switch=0
                        col27.space(1)
                        continue

        col11, col12 = st.columns([2,1])
        with col11:
            st.header("Features")
            artist_id = album_data[8]
            query = f"select a.album_name as 'Album Name', avg(c.danceability) as 'Danceability', avg(c.energy) as 'Energy', avg(c.liveness) as 'Liveness', avg(c.valence) as 'Valence', avg(c.speechiness) as 'Speechiness', avg(c.acousticness) as 'Acousticness', avg(c.instrumentalness) as 'Instrumentalness', a.album_id as 'Album ID' from albums_data a join tracks_data b on a.track_id = b.id join features_data c on b.id = c.id where artist_id = '{artist_id}' and (album_type = 'album' or album_type = 'compilation') group by a.album_id;"
            album_features_df = pd.read_sql_query(query, conn, index_col=['Album ID'])

            album_name = album_data[0]
            selected_rows = st.multiselect(label="Select Albums", options = album_features_df["Album Name"], default=[album_name] if album_name in album_features_df["Album Name"].values else [])
            filtered_df = album_features_df[album_features_df["Album Name"].isin(selected_rows)]
            st.line_chart(filtered_df.drop(columns=["Album Name"]).transpose())
        
        average_features_extra_query = f"select avg(avg_key), avg(avg_loudness), avg(avg_tempo) from (select a.album_name, avg(c.key) as avg_key, avg(c.loudness) as avg_loudness, avg(c.tempo) as avg_tempo from albums_data a join tracks_data b on a.track_id = b.id join features_data c on b.id = c.id where artist_id = '{artist_id}' and (album_type = 'album' or album_type = 'compilation') group by a.album_id);"
        
        cursor.execute(average_features_extra_query)
        average_features_extra = cursor.fetchone()

        album_fetures_extra_query = f"select avg(c.key), avg(c.loudness), avg(c.tempo) from albums_data a join tracks_data b on a.track_id = b.id join features_data c on b.id = c.id where album_id = '{album_id}';"                
        cursor.execute(album_fetures_extra_query)
        album_fetures_extra = cursor.fetchone()
        
        with col12:
            st.space(30)
            st.metric("Album Key", value = album_fetures_extra[0],  delta = f"{round(album_fetures_extra[0]-average_features_extra[0], 1)} vs Average Artist Album", format = "localized", border = True )
        
            st.metric("Album Loudness", value = f"{round(album_fetures_extra[1], 2)} Db",  delta = f"{round(album_fetures_extra[1]-average_features_extra[1], 2)} Db quiter vs Average Artist Album", format = "localized", border = True )
        
            st.metric("Album Tempo", value = f"{round(album_fetures_extra[2], 1)} BPM ",  delta = f"{round(album_fetures_extra[2]-average_features_extra[2], 1)} BPM vs Average Artist Album", format = "localized", border = True )

        #TRACKS
        st.space(4)
        track_number = None
        def change_track_number():
            if len(st.session_state["tracks_df"]["selection"]["cells"]) == 0:
                pass
            else:
                track_number = tracks_df.index[st.session_state["tracks_df"]["selection"]["cells"][0][0]]
                cursor.execute(f"select track_id from albums_data where track_number = '{track_number}' and album_id = '{album_id}';")
                track_id = cursor.fetchone()[0]
                st.session_state.track_id = track_id

        st.header("TRACKS")
        col16, col17 = st.columns(2)
        with col16:
            st.space(2)
            st.markdown("Please, select a track from the Tracklist to display information.")
            tracks_df = pd.read_sql_query(f"select a.track_number as 'Track Number', a.track_name as 'Track Name', b.track_popularity as 'Track Popularity' from albums_data a join tracks_data b on a.track_id = b.id where album_id = '{album_id}' order by track_number asc;", conn, index_col= ['Track Number'])
            st.dataframe(tracks_df['Track Name'],  on_select=change_track_number, selection_mode = "single-cell", key = "tracks_df")
        with col17:
            col22, col23, col24 = st.columns([1,4,1])
            with col23:
                st.subheader("Track Popularity Leaderboard", text_alignment = "center")
                st.dataframe(tracks_df.sort_values(by='Track Popularity', ascending= False)['Track Name'], hide_index= True)
            
        if track_id:
            track_data = return_tracks_data(track_id, False)
            display_track(track_data)
        else:
            track_data = return_tracks_data(None, True)
            display_track(track_data)

       

if "album_name" not in st.session_state:
    st.session_state.album_name = ""

if "artist_name_album_search" not in st.session_state:
    st.session_state.artist_name_album_search = ""

if "track_name" not in st.session_state:
    st.session_state.track_name = ""

if "album_id" not in st.session_state:
    st.session_state.album_id = ""

if "track_id" not in st.session_state:
    st.session_state.track_id = ""

if "tracks_df" not in st.session_state:
    st.session_state["tracks_df"] = None

col4, col5, col6, col7 = st.columns([3,3,3,1])
with col4:
    album_name_input = st.text_input("Album")
with col5:
    artist_name_album_search_input = st.text_input("Artist")
with col6:
    track_name_input = st.text_input("Track")
with col7:
    st.space("small")
    if st.button("Search", width = "stretch"):
        if album_name_input != "":
            st.session_state.album_name = album_name_input
        elif album_name_input == "":
            st.session_state.album_name = ""

        if artist_name_album_search_input != "":
            st.session_state.artist_name_album_search = artist_name_album_search_input
        elif artist_name_album_search_input == "":
            st.session_state.artist_name_album_search = ""

        if track_name_input != "":
            st.session_state.track_name = track_name_input
        elif track_name_input == "":
            st.session_state.track_name = ""

        st.rerun()

if st.session_state.album_name or st.session_state.artist_name_album_search or st.session_state.track_name:
    search_engine(st.session_state.album_name, st.session_state.artist_name_album_search, st.session_state.track_name)
elif st.session_state.album_id:
    display_data(st.session_state.album_id, st.session_state.track_id)
