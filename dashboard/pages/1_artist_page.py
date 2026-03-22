import streamlit as st
import requests
import sqlite3
from db import get_connection
import pandas as pd
from difflib import SequenceMatcher

st.set_page_config(page_title="Artist Lookup", layout="wide")
st.logo("supporting/logo.png", size = "large")
if st.sidebar.button("Business Tab"):
    st.session_state["play_event_planning_intro"] = True
    st.switch_page("pages/4_event_planning.py")

conn = get_connection()
cursor = conn.cursor()

with st.sidebar:
    use_genre_filter = st.toggle("Filter dashboard on genre")


    selectbox_option = st.sidebar.selectbox(
    "Looking for something specific?",
    ("Look up an Artist", "Look up an Album or a Track"),
    index = None,
    placeholder="Look up..."
    )
    if selectbox_option == "Look up an Artist":
        st.switch_page("pages/1_artist_page.py")
    elif selectbox_option == "Look up an Album or a Track":
        st.switch_page("pages/2_album_page.py")

    st.space("stretch")

    if st.sidebar.button("Business Tab"):
        st.session_state["play_event_planning_intro"] = True
        st.switch_page("pages/4_event_planning.py")

def get_artist_initial_data(artist, is_artist_name):
    if is_artist_name:
        query = f"select id, name, followers, genre_0, genre_1, genre_2 from artist_data where name = '{artist}' collate nocase;"
        cursor.execute(query)
        data = cursor.fetchall()
        return data
    else:
        query = f"select id, name, followers, genre_0, genre_1, genre_2 from artist_data where id = '{artist}';"
        cursor.execute(query)
        data = cursor.fetchone()
        return data

def name_similar_artists(artist, similarity_score):
    df = pd.read_sql_query("select id, name from artist_data;", conn, index_col= ['id'])

    similar_artists = []

    for index, row in df.iterrows():
        if SequenceMatcher(None, artist, row['name']).ratio() > similarity_score:
            similar_artists.append([index,row['name']])
    
    return similar_artists

def return_latest_album_picture(artist):
    refined_name = artist.replace(" ", "+")
    url = f"https://itunes.apple.com/search?term={refined_name}&entity=musicArtist&limit=1"
    data = requests.get(url).json()

    if data["resultCount"] > 0:
        result = data["results"][0]

        itunes_artist_id = result["artistId"]

        url = f"https://itunes.apple.com/lookup?id={itunes_artist_id}&entity=album"
        data = requests.get(url).json()

        albums = data["results"][1:]

        latest_album = max(albums, key=lambda x: x["releaseDate"])

        return latest_album["artworkUrl100"]
    else:
        return "https://imageio.forbes.com/specials-images/imageserve/5ed6636cdd5d320006caf841/The-Blackout-Tuesday-movement-is-causing-Instagram-feeds-to-turn-black-/0x0.jpg?width=960&dpr=2"

def search_similar_results(name):
    similar_artist_names = name_similar_artists(name, 0.65)

    if len(similar_artist_names) == 0:
        st.warning("There are no results found.")
    else:
        display_search_results(similar_artist_names)

def display_search_results(results):
    st.header("There are multiple outputs of the current search:")

    col20, col21, col22, col23 = st.columns(4)
    switch = 0
    for artist in results:
        if switch == 0:
            col20.image(return_latest_album_picture(artist[1]).replace("100x100","350x350"))
            switch+=1
            if col20.button(artist[1], key = artist[0], width = 350):
                modify_state(artist)
            col20.space("small")
        elif switch==1:
            col21.image(return_latest_album_picture(artist[1]).replace("100x100","350x350"))
            switch+=1
            if col21.button(artist[1], key = artist[0], width = 350):
                modify_state(artist)
            col21.space("small")
        elif switch==2:
            col22.image(return_latest_album_picture(artist[1]).replace("100x100","350x350"))
            switch+=1
            if col22.button(artist[1], key = artist[0], width = 350):
                modify_state(artist)
            col22.space("small")
        elif switch==3:
            col23.image(return_latest_album_picture(artist[1]).replace("100x100","350x350"))
            switch=0
            if col23.button(artist[1], key = artist[0], width = 350):
                modify_state(artist)
            col23.space("small")

def modify_state(result):
    st.session_state.artist_name = ""
    st.session_state.artist_id = result[0]
    st.rerun()
    
def search_engine(artist_name):
    data = get_artist_initial_data(artist_name, True)

    if len(data) == 0:
        search_similar_results(artist_name)
    elif len(data) > 1:
        display_search_results(data)
    else:
        display_data(data[0][0])

def display_data(artist_id): 
    data = get_artist_initial_data(artist_id, False)

    col3, col4 = st.columns([1,2])
    with col3:
        st.space("xsmall")
        st.image(return_latest_album_picture(data[1]).replace("100x100","320x320"))

    query = f"with sorted_artist_popularity as (select ROW_NUMBER() over (order by artist_popularity desc) as position, id, artist_popularity from artist_data) select position from sorted_artist_popularity where id = '{artist_id}';"
    cursor.execute(query)
    popularity_rank = cursor.fetchone()
    
    with col4:
        st.title(f"Meet {data[1]}", width = "stretch")
        col15, col16 = st.columns(2)
        with col15:
            if popularity_rank[0] == 1:
                st.badge("Top Performing Artist",color = "green")
            elif popularity_rank[0] == 2:
                st.badge("Second Top Performing Artist",color = "green")
            elif popularity_rank[0] == 3:
                st.badge("Third Top Performing Artist",color = "green")
            elif popularity_rank[0] >= 4 and popularity_rank[0] <= 10:
                st.badge(f"Top 10 Performing Artists",color = "green")
            elif popularity_rank[0] >= 11 and popularity_rank[0] <= 25:
                st.badge("Top 25 Performing Artists",color = "green")
            elif popularity_rank[0] >= 26 and popularity_rank[0] <= 50:
                st.badge("Top 50 Performing Artists",color = "green")
            elif popularity_rank[0] >= 51 and popularity_rank[0] <= 100:
                st.badge("Top 100 Performing Artists",color = "green")
            elif popularity_rank[0] >= 101 and popularity_rank[0] <= 200:
                st.badge("Top 200 Performing Artists",color = "green")
            elif popularity_rank[0] >= 201 and popularity_rank[0] <= 500:
                st.badge("Top 500 Performing Artists",color = "green")

            st.metric("Total Followers", data[2], format = "localized")

            st.metric("in the World", f"# {popularity_rank[0]}")
        with col16:
            cursor.execute(f"select avg(album_popularity) from (select album_name, album_popularity from albums_data where artist_id = '{artist_id}' and album_type = 'album' group by album_name);")
            albums_av_pop_total_album = cursor.fetchone()
            average_album_popularity = albums_av_pop_total_album[0]

            if average_album_popularity != None:
                query = f"select album_name, album_popularity from albums_data where artist_id = '{artist_id}' and album_type = 'album' group by album_name order by release_date desc limit 1;"
                cursor.execute(query)
                latest_album = cursor.fetchone()

                st.space("xxsmall")
                st.subheader("Latest Album Popularity")
                # st.text(latest_album)
                # st.text(latest_album[1])
                # st.text(average_album_popularity)
                st.metric(label =latest_album[0], value = latest_album[1], delta = f"{round((latest_album[1]-average_album_popularity),1)} vs average", border = True)
            
    #genre tab
    if data[3] != "":
        if data[4] != "":
            if data[5] != "":
                st.subheader("Top Genres")
                col5,col6,col7 = st.columns(3)
                with col5:
                    st.metric(label = "not shown", label_visibility="collapsed", value = data[3], border = True )
                with col6:
                    st.metric(label = "not shown", label_visibility="collapsed", value = data[4], border = True )
                with col7:
                    st.metric(label = "not shown", label_visibility="collapsed", value = data[5], border = True )
            else:
                st.subheader("Top Genres")
                col5,col6 = st.columns(2)
                with col5:
                    st.metric(label = "not shown", label_visibility="collapsed", value = data[3], border = True )
                with col6:
                    st.metric(label = "not shown", label_visibility="collapsed", value = data[4], border = True )
        else:
            st.subheader("Top Genres")
            st.metric(label = "not shown", label_visibility="collapsed", value = data[3], border = True )

    #Album Popularity
    options = ["Albums", "Compilations"]
    selection = st.pills(label_visibility="collapsed", label = "not shown",options = options, selection_mode="multi", default = "Albums")
    if len(selection) == 0:
        pass
    elif selection[0] and len(selection) ==1:
        album_type = None
        if selection[0] == "Albums":
            st.header("ALBUMS")
            album_type = "Album"
        else:
            st.header("COMPILATIONS")
            album_type = "Compilation"

        df_album_pop_1 = pd.read_sql_query(f"""select album_popularity as "{album_type} Popularity", album_name as "{album_type} Name", count(album_name) as 'Number of Tracks' from albums_data where artist_id = "{artist_id}" and album_type = "{album_type}" collate nocase group by album_name order by album_popularity desc;""", conn)

        if len(df_album_pop_1) > 0:
            col8, col9 = st.columns(2)
            with col8:
                st.subheader(f"{selection[0]} Performance")
                #move this one above and implement and if statement with len = 0
                
                st.dataframe(df_album_pop_1, hide_index=True)
            with col9:
                df_album_pop_2 = pd.read_sql_query(f"select Year, avg(album_popularity) as Popularity from (select album_name, substring(release_date,1,4) as Year, album_popularity from albums_data where artist_id = '{artist_id}' and album_type = '{album_type}' collate nocase group by album_name) group by year order by year asc;", conn, index_col= ['Year'])
                if len(df_album_pop_2) > 1:  
                    st.space("xxsmall")
                    st.subheader(f"{selection[0]} Popularity")
                    st.space("xsmall")
                    st.line_chart(df_album_pop_2, y_label = f'{selection[0]} Popularity', height = 'stretch')
            col17,col18,col19 = st.columns(3)
            cursor.execute(f"select avg(album_popularity), count(*), avg(album_length) from (select album_name, album_popularity, sum(duration_sec) as album_length from albums_data where artist_id = '{artist_id}' and album_type = '{album_type}' collate nocase group by album_name);")
            albums_av_pop_total_album_type = cursor.fetchone()
            average_album_type_popularity = albums_av_pop_total_album_type[0]
            total_albums_type = albums_av_pop_total_album_type[1]
            albums_type_length = albums_av_pop_total_album_type[2]
            with col17:
                st.metric(f"Total {selection[0]}", value = total_albums_type, border = True , format = "localized")
            with col18:    
                st.metric(f"Average {album_type} Length", value = f"{int(albums_type_length//60)}min {int(albums_type_length%60)} sec", border = True )
            with col19:
                st.metric(f"Average {album_type} Popularity", value = round(average_album_type_popularity), border = True )

            #albums tempo comparison
            st.subheader("Album Tempo")
            df_tempos = pd.read_sql_query(f"select avg(c.tempo) as Tempo, a.album_name as 'Album Name' from albums_data a join tracks_data b on a.track_id = b.id join features_data c on b.id = c.id where a.artist_id = '{artist_id}' and album_type = '{album_type}' collate nocase group by album_name;", conn, index_col= ['Album Name'])
            st.bar_chart(df_tempos)
        else:
            st.subheader(f"There are no {album_type}.")
    elif selection[0] and selection[1]:
        st.header("ALBUMS & COMPILATIONS")

        both = "Albums & Compilations"
        album_type_1 = "Album"
        album_type_2 = "Compilation"
        df_album_pop_1 = pd.read_sql_query(f"""select album_popularity as "Item Popularity", album_name as "{both} Name", count(album_name) as 'Number of Tracks' from albums_data where artist_id = "{artist_id}" and (album_type = "{album_type_1}" collate nocase or album_type = "{album_type_2}" collate nocase) group by album_name order by album_popularity desc;""", conn)
        if len(df_album_pop_1)> 0:
            col8, col9 = st.columns(2)
            with col8:
                st.subheader(f"{both} Performance")
                st.dataframe(df_album_pop_1, hide_index=True)
            with col9:
                df_album_pop_2 = pd.read_sql_query(f"select Year, avg(album_popularity) as Popularity from (select album_name, substring(release_date,1,4) as Year, album_popularity from albums_data where artist_id = '{artist_id}' and (album_type = '{album_type_1}' collate nocase or album_type = '{album_type_2}' collate nocase) group by album_name) group by year order by year asc;", conn, index_col= ['Year'])
                if len(df_album_pop_2) > 1:
                    st.space("xxsmall")
                    st.subheader(f"{both} Popularity")
                    st.space("xsmall")
                    st.line_chart(df_album_pop_2, y_label = f'{both} Popularity', height = 'stretch')

            col17,col18,col19 = st.columns(3)
            cursor.execute(f"select avg(album_popularity), count(*), avg(album_length) from (select album_name, album_popularity, sum(duration_sec) as album_length from albums_data where artist_id = '{artist_id}' and (album_type = '{album_type_1}' collate nocase or album_type = '{album_type_2}' collate nocase) group by album_name);")
            albums_av_pop_total_album_type = cursor.fetchone()
            average_album_type_popularity = albums_av_pop_total_album_type[0]
            total_albums_type = albums_av_pop_total_album_type[1]
            albums_type_length = albums_av_pop_total_album_type[2]
            with col17:
                st.metric(f"Total {both}", value = total_albums_type, border = True , format = "localized")
            with col18:    
                st.metric(f"Average {both} Length", value = f"{int(albums_type_length//60)}min {int(albums_type_length%60)} sec", border = True )
            with col19:
                st.metric(f"Average {both} Popularity", value = round(average_album_type_popularity), border = True )

            #albums tempo comparison
            st.subheader("Album Tempo")
            df_tempos = pd.read_sql_query(f"select avg(c.tempo) as Tempo, a.album_name as 'Album Name' from albums_data a join tracks_data b on a.track_id = b.id join features_data c on b.id = c.id where a.artist_id = '{artist_id}' and (album_type = '{album_type_1}' collate nocase or album_type = '{album_type_2}' collate nocase) group by album_name;", conn, index_col= ['Album Name'])
            st.bar_chart(df_tempos, y_label = "BPM")
        else:
            st.subheader(f"There are no {both}.")

    #Track metrics
    st.header("TRACKS")
    col10, col11, col12 = st.columns(3)

    cursor.execute(f"select count(track_id), avg(duration_sec), avg(track_popularity) from albums_data a join tracks_data b on a.track_id = b.id where artist_id = '{artist_id}';")
    tracks_metrics = cursor.fetchone()

    with col10:
        st.metric("Total Tracks", value = tracks_metrics[0], border = True , format = "localized")
    with col11: 
        st.metric("Average Track Length", value = f"{int(tracks_metrics[1]//60)} min {int(tracks_metrics[1]%60)} sec", border = True )
    with col12:
        st.metric("Average Track Popularity", value = round(tracks_metrics[2]), border = True )
    
    col13, col14 = st.columns(2)
    with col13:
        st.subheader("Tracks Performance")
        df_tracks = pd.read_sql_query(f"select b.track_popularity 'Track Popularity', a.track_name as 'Track Name' from albums_data a join tracks_data b on a.track_id = b.id where artist_id = '{artist_id}' order by b.track_popularity desc;", conn, index_col=['Track Name'])
        st.dataframe(df_tracks)

    with col14:
        st.subheader("Top 3 Tracks Characteristics")
        df_tracks_specs = pd.read_sql_query(f"select a.track_name as 'Track Name', c.danceability as 'Danceability', c.energy as 'Energy', c.liveness as 'Liveness', c.valence as 'Valence', c.speechiness as 'Speechiness', c.acousticness as 'Acousticness', c.instrumentalness from albums_data a join tracks_data b on a.track_id = b.id join features_data c on b.id = c.id where artist_id = '{artist_id}' order by b.track_popularity desc limit 3;", conn, index_col=['Track Name']).transpose()
        st.space("xsmall")
        st.line_chart(df_tracks_specs)

try:
    if "artist_name" not in st.session_state:
        st.session_state.artist_name = ""
    if "artist_id" not in st.session_state:
        st.session_state.artist_id = ""

    col24, col25 = st.columns([10,1])
    with col24:
        artist_name_input = st.text_input("Enter Artist")
    with col25:
        st.space("small")
        if st.button("Search", width = "stretch"):
            st.session_state.artist_name = artist_name_input
            st.session_state.artist_id = ""
            st.rerun()

    if st.session_state.artist_name:
        search_engine(st.session_state.artist_name)
    elif st.session_state.artist_id:
        display_data(st.session_state.artist_id)
except Exception as e:
    st.error(f"There seems to be an unexpected error!: {e}")