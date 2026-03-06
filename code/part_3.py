import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import part_3_functions as func
from typing import Dict, List


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

"""
Mark's Part
"""
def analyze_artists_in_top_feature_percent(con, feature):

    q_count = f"SELECT COUNT(*) as total FROM features_data"
    total_tracks = pd.read_sql(q_count, con)["total"][0]
    top_n = int(total_tracks * 0.10)

    query = f"""
    SELECT
        features_data.id AS track_id,
        features_data.{feature} AS feature_value,
        artist_data.name AS artist_name
    FROM features_data
    JOIN tracks_data
        ON tracks_data.id = features_data.id
    JOIN albums_data
        ON albums_data.track_id = tracks_data.id
    JOIN artist_data
        ON artist_data.id = albums_data.artist_id
    ORDER BY features_data.{feature} DESC LIMIT {top_n}
    """

    top_tracks = pd.read_sql(query, con)

    artist_counts = (
        top_tracks.groupby("artist_name").size().reset_index(name="n_tracks").sort_values("n_tracks", ascending=False)
    )

    print("Top 10% tracks:", top_n)
    print("\nArtists appearing most in top 10%:")
    print(artist_counts.head(15))

print(analyze_artists_in_top_feature_percent(con, "danceability"))

BROAD_GENRES = [
    "Hip-Hop",
    "R&B",
    "Raggae",
    "Latin",
    "Jazz",
    "Classical",
    "Country",
    "Rock",
    "Electronic Dance Music (EDM)",
    "Indie/Experimental",
    "Pop",
]

GENRE_KEYWORDS: Dict[str, List[str]] = {
    "Pop": [
            "pop", "idol",
        ],
    "Rock": [
        "rock", "punk", "metal", "emo", "grunge", "gaze",
        "hardcore", "screamo", "thrash", "doom", "sludge",
        "djent", "metal", "deathcore",
        "grindcore", "rockabilly", "britpop",
        ],
    "Hip-Hop": [
        "hip-hop", "hiphop", "hip hop", "rap", "trap", "drill", "grime", "phonk",
        "bap", "boom", "gangsta", "hyphy", "crunk", "turntablism",
        "plugg",
        ],
    "R&B": [
        "rnb", "soul", "funk", "motown", "r&b",
        ],
    "Jazz": [
        "jazz", "bebop", "bop", "swing", "dixieland", "big band",
        ],
    "Indie/Experimental": [
        "indie", "experimental", "ambient", "lo fi", "lofi", "noise", "drone",
        "glitch", "idm", "industrial", "electroacoustic", "acousmatic",
        "avant", "microtonal", "hauntology", "outsider", "abstract",
        ],
    "Electronic Dance Music (EDM)": [
        "edm", "electronic", "electronica", "electro", "techno", "house",
        "trance", "dnb", "d&b","drum and base","dubstep", "breakbeat", "breakcore", "rave",
        "hardstyle", "gabber", "jungle", "ukg", "garage", "bassline",
        "synth", "synthwave", "synthpop", "complextro",
        ],
    "Latin": [
        "latin", "reggaeton", "salsa", "bachata", "cumbia", "merengue",
        "vallenato", "bolero", "bossa", "samba", "tango", "mariachi",
        "corridos", "norteno", "tejano", "ranchera", "tex mex", "urbano",
        "mpb",
        ],
    "Raggae": [
        "reggae", "dancehall", "ska", "rocksteady", "riddim",
        ],
    "Country": [
        "country", "americana", "bluegrass", "honky", "banjo", "fiddle",
        "cowboy", "outlaw", "redneck", "bakersfield",
        ],
    "Classical": [
        "classical", "baroque", "opera", "orchestra", "symphony",
        "choir", "choral", "chamber", "renaissance", "romantic",
        "impressionism", "gregorian",
        "piano", "violin", "cello", "clarinet", "trombone", "trumpet",
        "tenor", "soprano",
        ]
}


def map_broad_genres(con, genre_keywords: Dict[str, List[str]] = GENRE_KEYWORDS):

    genre_cols = [f"genre_{i}" for i in range(7)]
    cols = ["id", "name"] + genre_cols
    artists = pd.read_sql_query(f"SELECT {', '.join(cols)} FROM artist_data",con)

    def classify_row(row) -> List[str]:
        genres = []
        for column in genre_cols:
            value = row[column]
            if isinstance(value, str) and value != "":
                genres.append(value.lower())

        matched = []
        for broad, keywords in genre_keywords.items():
            for keyword in keywords:
                keyword = keyword.lower()
                if any(keyword in genre for genre in genres):
                    matched.append(broad)
                    break

        return matched

    artists["broad_genres"] = artists.apply(classify_row, axis=1)

    for genre in BROAD_GENRES:
        artists[genre] = artists["broad_genres"].apply(lambda lst: int(genre in lst))

    return artists[["id", "name","genre_0", "genre_1", "genre_2", "genre_3", "genre_4", "genre_5","genre_6", "broad_genres"] +BROAD_GENRES]

df = map_broad_genres(con)
print(df[["name", "broad_genres"]].head(50).to_string(index=False))
