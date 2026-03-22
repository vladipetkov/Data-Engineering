import sqlite3
import pandas as pd
from typing import Dict, List


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
            "pop", "idol"],
    "Rock": [
        "rock", "punk", "metal", "emo", "grunge", "gaze",
        "hardcore", "screamo", "thrash", "doom", "sludge",
        "djent", "metal", "deathcore", "grindcore", "rockabilly", "britpop"],
    "Hip-Hop": [
        "hip-hop", "hiphop", "hip hop", "rap", "trap", "drill", "grime", "phonk",
        "bap", "boom", "gangsta", "hyphy", "crunk", "turntablism","plugg"],
    "R&B": [
        "rnb", "soul", "funk", "motown", "r&b"],
    "Jazz": [
        "jazz", "bop", "swing", "dixieland", "big band", "blues"],
    "Indie/Experimental": [
        "indie", "experimental", "ambient","lo-fi" "lo fi", "lofi", "noise", "drone",
        "glitch", "idm", "industrial", "electroacoustic", "acousmatic",
        "avant", "microtonal", "hauntology", "outsider", "abstract"],
    "Electronic Dance Music (EDM)": [
        "edm", "electronic", "electronica", "electro", "techno", "house",
        "trance", "dnb", "d&b","drum and base","dubstep", "breakbeat", "breakcore", "rave",
        "hardstyle", "gabber", "jungle", "ukg", "bassline",
        "synth", "synthwave", "synthpop", "complextro"],
    "Latin": [
        "latin", "salsa", "bachata", "cumbia", "merengue",
        "vallenato", "bolero", "bossa", "samba", "tango", "mariachi",
        "corridos", "norteno", "tejano", "ranchera", "tex mex", "urbano","mpb"],
    "Raggae": [
        "reggae","reggaeton", "dancehall", "ska", "rocksteady", "riddim"],
    "Country": [
        "country", "americana", "bluegrass", "honky", "banjo", "fiddle",
        "cowboy", "outlaw", "redneck", "bakersfield"],
    "Classical": [
        "classical", "baroque", "opera", "orchestra", "symphony",
        "choir", "choral", "chamber", "renaissance","impressionism", "gregorian",
        "piano", "violin", "cello", "clarinet", "trombone", "trumpet","tenor", "soprano"]
}


def map_broad_genres(
    database_path: str,
    genre_keywords: Dict[str, List[str]] = GENRE_KEYWORDS):
# Maps detailed Spotify-style genres into a smaller set of broad genres
    conn = sqlite3.connect(database_path)

    genre_cols = [f"genre_{i}" for i in range(7)]
    cols = ["id", "name"] + genre_cols
    artists = pd.read_sql_query(f"SELECT {', '.join(cols)} FROM artist_data",conn)
    conn.close()

    def classify_row(row):
        genres = []
        for c in genre_cols:
            val = row[c]
            if isinstance(val, str) and val != "":
                genres.append(val.lower())

        matched = []
        for broad, keywords in genre_keywords.items():
            for kw in keywords:
                kw = kw.lower()
                if any(kw in g for g in genres):
                    matched.append(broad)
                    # don't add same broad genre twice
                    break

        return matched

    artists["broad_genres"] = artists.apply(classify_row, axis=1)

    # one-hot columns
    for g in BROAD_GENRES:
        artists[g] = artists["broad_genres"].apply(lambda lst: int(g in lst))

    return artists[["id", "name", "broad_genres"] + BROAD_GENRES]


#if __name__ == "__main__":
    df = map_broad_genres("spotify_database.db")
    print(df[["name", "broad_genres"]].head(50).to_string(index=False))
