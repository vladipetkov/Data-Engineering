import sqlite3
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from db import get_connection
from genre_mapper import map_broad_genres
from genre_mapper import GENRE_KEYWORDS as GK, BROAD_GENRES as BROAD_GENRE_LIST
from pathlib import Path

logo_path = Path(__file__).parent / "supporting" / "logo.png"
st.logo(logo_path, size = "large")
st.set_page_config(page_title="Spotify Dashboard", layout="wide")

GENRE_KEYWORDS = {
    "Pop": [
        "pop", "idol",
    ],
    "Rock": [
        "rock", "punk", "metal", "emo", "grunge", "gaze",
        "hardcore", "screamo", "thrash", "doom", "sludge",
        "djent", "deathcore", "grindcore", "rockabilly", "britpop",
    ],
    "Hip-Hop": [
        "hip-hop", "hiphop", "hip hop", "rap", "trap", "drill", 
        "grime", "phonk", "bap", "boom", "gangsta", "hyphy", 
        "crunk", "turntablism", "plugg",
    ],
    "R&B": [
        "rnb", "soul", "funk", "motown", "r&b",
    ],
    "Jazz": [
        "jazz", "bebop", "bop", "swing", "dixieland", "big band",
    ],
    "Indie/Experimental": [
        "indie", "experimental", "ambient", "lofi", "noise", 
        "drone", "glitch", "idm", "industrial", "electroacoustic", 
        "acousmatic", "avant", "microtonal", "hauntology", 
        "outsider", "abstract",
    ],
    "Electronic Dance Music (EDM)": [
        "edm", "electronic", "electronica", "electro", "techno", 
        "house", "trance", "dnb", "d&b", "drum and bass", "dubstep", 
        "breakbeat", "breakcore", "rave", "hardstyle", "gabber", 
        "jungle", "ukg", "garage", "bassline", "synth", "synthwave", 
        "synthpop", "complextro",
    ],
    "Latin": [
        "latin", "reggaeton", "salsa", "bachata", "cumbia", "merengue",
        "vallenato", "bolero", "bossa", "samba", "tango", "mariachi",
        "corridos", "norteno", "tejano", "ranchera", "tex mex", 
        "urbano", "mpb",
    ],
    "Reggae": [
        "reggae", "dancehall", "ska", "rocksteady", "riddim",
    ],
    "Country": [
        "country", "americana", "bluegrass", "honky", "banjo", 
        "fiddle", "cowboy", "outlaw", "redneck", "bakersfield",
    ],
    "Classical": [
        "classical", "baroque", "opera", "orchestra", "symphony",
        "choir", "choral", "chamber", "renaissance", "romantic",
        "impressionism", "gregorian", "piano", "violin", "cello", 
        "clarinet", "trombone", "trumpet", "tenor", "soprano",
    ],
}

conn = get_connection()
cursor = conn.cursor()

with st.sidebar:
    use_genre_filter = st.toggle("Filter dashboard on genre")
    
    if use_genre_filter:
        options = list(GENRE_KEYWORDS.keys())
        selection = st.pills("Genres", options, selection_mode="multi", disabled=not use_genre_filter)

    if not use_genre_filter:
        selection = []
        st.sidebar.caption("Showing all genres")

    st.space(8)

    selectbox_option = st.sidebar.selectbox(
    "Looking for something specific?",
    ("Look up an Artist", "Look up an Album or a Track"),
    index = None,
    placeholder="Look up..."
    )

    artist_file_path = Path(__file__).parent / "pages" / "1_artist_page.py"
    albums_file_path = Path(__file__).parent / "pages" / "2_album_page.py"
    if selectbox_option == "Look up an Artist":
        st.switch_page(artist_file_path)
    elif selectbox_option == "Look up an Album or a Track":
        st.switch_page(albums_file_path)

    st.space(400)
    business_tab_file_path = Path(__file__).parent / "pages" / "4_event_planning.py"
    if st.sidebar.button("Business Tab", type = "primary", width = "stretch"):
        st.session_state["play_event_planning_intro"] = True
        st.switch_page(business_tab_file_path)

if not use_genre_filter or not selection:
    keywords = []
else:
    keywords = [kw for genre in selection for kw in GENRE_KEYWORDS[genre]]

# Genre title
if not use_genre_filter or not selection: 
    st.title(f"General")

elif len(selection) == 1:
    st.title(f"{selection[0]}")

else:
    st.title(f"{len(selection)} Genres selected") 

#creates a where clause from the keywords from the genre filter
def where_selected_genres(keywords):
    if not keywords:
        return "", []
    
    genre_cols = ["genre_0", "genre_1", "genre_2", "genre_3", "genre_4", "genre_5", "genre_6", "artist_genres"]
    conditions = []
    params = []
    for col in genre_cols:
        for kw in keywords:
            conditions.append(f"LOWER(a.{col}) LIKE ?")
            params.append(f"%{kw}%")    
    return "WHERE " + " OR ".join(conditions), params


def get_kpis(keywords):
    where, params = where_selected_genres(keywords)  
    cursor.execute(f"""                             
        SELECT 
            COUNT(DISTINCT a.id) AS total_artists,
            AVG(a.followers) AS avg_fol,
            AVG(a.artist_popularity) AS avg_pop,
            AVG(t.track_popularity) AS avg_track_pop
        FROM artist_data a
        JOIN albums_data al ON al.artist_id = a.id
        JOIN tracks_data t ON t.id = al.track_id
        {where}""", params) 
    rows = cursor.fetchall()
    return pd.DataFrame(rows, columns=[x[0] for x in cursor.description])


def top_artists_popularity(keywords):
    where, params = where_selected_genres(keywords)
    cursor.execute(f"""
        SELECT DISTINCT a.name, a.artist_popularity
        FROM artist_data a
        JOIN albums_data al ON al.artist_id = a.id
        JOIN tracks_data t  ON t.id = al.track_id
        {where}
        ORDER BY a.artist_popularity DESC
        LIMIT 100""",params)
    
    rows = cursor.fetchall()
    return pd.DataFrame(rows, columns=["Artist", "Popularity"])


def top_artists_followers(keywords):
    where, params = where_selected_genres(keywords)
    cursor.execute(f"""
        SELECT DISTINCT a.name, a.followers
        FROM artist_data a
        JOIN albums_data al ON al.artist_id = a.id
        JOIN tracks_data t  ON t.id = al.track_id
        {where}
        ORDER BY a.followers DESC
        LIMIT 100""", params)
    rows = cursor.fetchall()
    return pd.DataFrame(rows, columns=["Artist", "Followers"])    

def top_albums_popularity(keywords):
    where, params = where_selected_genres(keywords)
    cursor.execute(f"""
        SELECT DISTINCT al.album_name, a.name AS artist, al.album_popularity
        FROM artist_data a
        JOIN albums_data al ON al.artist_id = a.id
        JOIN tracks_data t  ON t.id = al.track_id
        {where}
        ORDER BY al.album_popularity DESC
        LIMIT 100""", params)      
     
    rows = cursor.fetchall()
    return pd.DataFrame(rows, columns=["Album", "Artist", "Popularity"])

def heatmap(keywords):
    where, params = where_selected_genres(keywords)
    where_2023 = f"{'AND' if where else 'WHERE'} al.release_date LIKE '2023%'"
    cursor.execute(f"""
        SELECT DISTINCT al.album_name, al.release_date
        FROM artist_data a
        JOIN albums_data al ON al.artist_id = a.id
        JOIN tracks_data t  ON t.id = al.track_id
        {where}
        {where_2023}""", params)
    
    rows = cursor.fetchall()
    return pd.DataFrame(rows, columns=["Album", "release_date"])
    
def track_duration(keywords):
    where, params = where_selected_genres(keywords)
    cursor.execute(f"""
        SELECT 
            f.duration_ms,
            CASE
                WHEN al.release_date BETWEEN '1983-01-01' AND '1992-12-31' THEN '83–93'
                WHEN al.release_date BETWEEN '1993-01-01' AND '2002-12-31' THEN '93–03'
                WHEN al.release_date BETWEEN '2003-01-01' AND '2012-12-31' THEN '03–13'
                WHEN al.release_date BETWEEN '2013-01-01' AND '2023-12-31' THEN '13–23'
            END AS decade
        FROM artist_data a
        JOIN albums_data al ON al.artist_id = a.id
        JOIN tracks_data t  ON t.id = al.track_id 
        JOIN features_data f ON f.id = t.id
        {where}""", params)      
    
    rows = cursor.fetchall()
    return pd.DataFrame(rows, columns=["duration_ms", "decade"])

def get_genre_popularity(keywords, year_start, year_end):
    where, params = where_selected_genres(keywords)
    year_clause = f"{'AND' if where else 'WHERE'} CAST(SUBSTR(al.release_date, 1, 4) AS INTEGER) BETWEEN ? AND ?"
    genre_cols = [f"genre_{i}" for i in range(7)]
    cursor.execute(f"""
        SELECT
            CAST(SUBSTR(al.release_date, 1, 4) AS INTEGER) AS year,
            {", ".join([f"a.{c}" for c in genre_cols])},
            AVG(t.track_popularity) AS avg_pop
        FROM artist_data a
        JOIN albums_data al ON al.artist_id = a.id
        JOIN tracks_data t  ON t.id = al.track_id
        {where}
        {year_clause}
        GROUP BY year, {", ".join([f"a.{c}" for c in genre_cols])}
    """, params + [year_start, year_end])
    rows = cursor.fetchall()
    col_names = ["year"] + genre_cols + ["avg_pop"]
    return pd.DataFrame(rows, columns=col_names)


# 4 metrics: total artists, avg followers, avg artist popularity, avg track popularity
kpis = get_kpis(keywords)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric("Total artists", f"{int(kpis['total_artists'][0]):,}")
kpi2.metric("Avg Followers",f"{int(kpis['avg_fol'][0]):,}")
kpi3.metric("Avg Artist Popularity",f"{int(kpis['avg_pop'][0])}")
kpi4.metric("Avg Track Popularity",f"{int(kpis['avg_track_pop'][0])}")

st.divider()

# Top 100's

top1, top2, top3 = st.columns(3)

with top1:
    st.subheader("Most Popular Artists")
    df_1 = top_artists_popularity(keywords)
    df_1.insert(0, '#', range(1, len(df_1) + 1))
    st.dataframe(
        df_1[["#", "Artist"]],
        hide_index=True,
        use_container_width=True,
        height=500)
        
with top2:
    st.subheader("Most Followed Artists")
    df_2 = top_artists_followers(keywords)
    df_2.insert(0, '#', range(1, len(df_2) + 1))
    df_2["Followers"] = df_2["Followers"].apply(lambda x: f"{int(x):,}")
    st.dataframe(
        df_2[["#", "Artist", "Followers"]],
        hide_index=True,
        use_container_width=True,
        height=500)
    
with top3:
    st.subheader("Most Popular Albums")
    df_3 = top_albums_popularity(keywords)
    df_3.insert(0, '#', range(1, len(df_3) + 1))
    st.dataframe(
        df_3[["#", "Album", "Artist"]],
        hide_index=True,
        use_container_width=True,
        height=500)

st.divider()

# Heatmap
df = heatmap(keywords)
df["release_date"] = pd.to_datetime(df["release_date"])

daily_counts = df.groupby(df["release_date"].dt.date).size().reset_index(name="count")
daily_counts["date"] = pd.to_datetime(daily_counts["release_date"])
daily_counts["weekday"] = daily_counts["date"].dt.weekday
daily_counts["week"] = daily_counts["date"].dt.isocalendar().week

heatmap_data = daily_counts.pivot_table(index="weekday", columns="week", values="count", aggfunc="sum")
heatmap_data.index = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]  

fig, ax = plt.subplots(figsize=(12, 4))
sns.heatmap(heatmap_data, cmap="YlOrRd", linewidths=0.5, ax=ax)
ax.set_title("Album Releases Heatmap")
ax.set_ylabel("Weekday")
ax.set_xlabel("Week Number")

fig, ax = plt.subplots(figsize=(12, 4))

fig.patch.set_facecolor("#1A2F32")
ax.set_facecolor("#1A2F32")

sns.heatmap(heatmap_data, cmap="YlOrRd", linewidths=0.5, ax=ax,
            linecolor="#1A2F32")

ax.set_title("Album Releases Heatmap", color="white")
ax.set_ylabel("Weekday", color="white")
ax.set_xlabel("Week Number", color="white")
ax.tick_params(colors="white")

ax.collections[0].colorbar.ax.tick_params(colors="white")
ax.collections[0].colorbar.ax.yaxis.label.set_color("white")

st.pyplot(fig)

st.divider()

### Graphs

# Monthly album releases

monthly_counts = df.groupby(df["release_date"].dt.month).size().reset_index(name="count")
monthly_counts.columns = ["month", "count"]
monthly_counts["month_name"] = pd.to_datetime(monthly_counts["month"], format="%m").dt.strftime("%b")

fig2, ax2 = plt.subplots(figsize=(12, 4))
fig2.patch.set_facecolor("#1A2F32")
ax2.set_facecolor("#1A2F32")

ax2.bar(monthly_counts["month_name"], monthly_counts["count"], color="#a8d5a2")

ax2.set_title("Monthly Album Releases 2023", color="white")
ax2.set_xlabel("Month", color="white")
ax2.set_ylabel("Releases", color="white")
ax2.tick_params(colors="white")
ax2.spines[:].set_color("#1A2F32")

st.pyplot(fig2)

st.divider()
 
# piechart genre partition

col_pie, col_box = st.columns(2)
 
with col_pie:
    st.subheader("Genre Distribution")
    genre_df = map_broad_genres()
 
    counts = {g: genre_df[g].sum() for g in BROAD_GENRE_LIST if g in genre_df.columns}
    counts = {k: v for k, v in counts.items() if v > 0}
 
    labels = list(counts.keys())
    sizes  = list(counts.values())
 
    greens = [
        "#1a7a1a", "#2d9e2d", "#40b840", "#66c466", "#8cd08c",
        "#a8d5a2", "#c5e8c5", "#1f5e1f", "#3b8c3b", "#d4f0d4", "#0f4f0f",
    ]
 
    fig_pie, ax_pie = plt.subplots(figsize=(5, 4))
    fig_pie.patch.set_facecolor("#1A2F32")
    ax_pie.set_facecolor("#1A2F32")
    wedges, texts, autotexts = ax_pie.pie(
        sizes,
        labels=labels,
        autopct="%1.1f%%",
        colors=greens[: len(labels)],
        startangle=140,
        textprops={"color": "white", "fontsize": 7},
    )
    for at in autotexts:
        at.set_fontsize(6.5)
    ax_pie.set_title("Broad Genre Split", color="white", fontsize=10)
    plt.tight_layout()
    st.pyplot(fig_pie)
 
# Track duration boxplot

with col_box:
    st.subheader("Track Duration by Decade")
    df_dur = track_duration(keywords)
    df_dur = df_dur.dropna(subset=["decade"])
    df_dur["duration_min"] = df_dur["duration_ms"] / 60000
 
    order = ["83–93", "93–03", "03–13", "13–23"]
 
    fig_box, ax_box = plt.subplots(figsize=(5, 4))
    fig_box.patch.set_facecolor("#1A2F32")
    ax_box.set_facecolor("#1A2F32")
 
    sns.boxplot(
        x="decade", y="duration_min", data=df_dur,
        order=order,
        palette=["#a8d5a2"],
        ax=ax_box,
        showfliers=False,
    )
 
    ax_box.set_ylim(0, 10)
    ax_box.set_xlabel("Decade", color="white")
    ax_box.set_ylabel("Duration (minutes)", color="white")
    ax_box.set_title("Track Duration by Decade", color="white")
    ax_box.tick_params(colors="white")
    ax_box.spines[:].set_color("#1A2F32")
    plt.tight_layout()
    st.pyplot(fig_box)
 
st.divider()

# Genre popularity development with timeslider

st.subheader("Genre Popularity Over Time")
 
year_start, year_end = st.slider(
    "Select period",
    min_value=1973,
    max_value=2023,
    value=(1973, 2023),
    key="slider_genre_time",
)
 
df_time = get_genre_popularity(keywords, year_start, year_end)
 
genre_cols_list = [f"genre_{i}" for i in range(7)]
 
def classify_broad(row):
    vals = [str(row[c]).lower() for c in genre_cols_list if isinstance(row[c], str) and row[c]]
    for broad, kws in GK.items():
        if any(kw in v for v in vals for kw in kws):
            return broad
    return None
 
df_time["broad_genre"] = df_time.apply(classify_broad, axis=1)
df_time = df_time.dropna(subset=["broad_genre"])
 
fig_line, ax_line = plt.subplots(figsize=(14, 5))
fig_line.patch.set_facecolor("#1A2F32")
ax_line.set_facecolor("#1A2F32")
 
greens_line = [
    "#1a7a1a", "#2d9e2d", "#40b840", "#66c466", "#8cd08c",
    "#a8d5a2", "#c5e8c5", "#1f5e1f", "#3b8c3b", "#d4f0d4", "#0f4f0f",
]
 
if not selection:
    general = df_time.groupby("year")["avg_pop"].mean().reset_index()
    ax_line.plot(general["year"], general["avg_pop"],
                 label="General Popularity", color="#a8d5a2", linewidth=2)
else:
    general = df_time.groupby("year")["avg_pop"].mean().reset_index()
    ax_line.plot(general["year"], general["avg_pop"],
                 label="General", color="white", linewidth=1,
                 linestyle="--", alpha=0.35)
 
    genre_data = df_time[df_time["broad_genre"].isin(selection)]
    line_data = (
        genre_data.groupby(["year", "broad_genre"])["avg_pop"]
        .mean()
        .reset_index()
    )
    for i, genre in enumerate(selection):
        subset = line_data[line_data["broad_genre"] == genre]
        if subset.empty:
            continue
        ax_line.plot(subset["year"], subset["avg_pop"],
                     label=genre, color=greens_line[i % len(greens_line)], linewidth=2)
 
ax_line.set_xlabel("Year", color="white")
ax_line.set_ylabel("Avg Track Popularity", color="white")
ax_line.set_title("Genre Popularity Over Time", color="white")
ax_line.tick_params(colors="white")
ax_line.spines[:].set_color("#2a4f52")
ax_line.legend(
    fontsize=7,
    facecolor="#1A2F32",
    labelcolor="white",
    framealpha=0.5,
    loc="upper left",
)
plt.tight_layout()
st.pyplot(fig_line)
