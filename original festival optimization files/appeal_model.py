import sqlite3
import numpy as np
import pandas as pd


def _minmax_0_100(s: pd.Series) -> pd.Series:
# Rescales a series to a 0-100 range
    s = pd.to_numeric(s).fillna(0.0)
    if len(s) == 0:
        return pd.Series(dtype=float)

    s_min = s.min()
    s_max = s.max()

    if pd.isna(s_min) or pd.isna(s_max) or s_max == s_min:
        return pd.Series(np.zeros(len(s)), index=s.index, dtype=float)

    return 100.0 * (s-s_min)/(s_max-s_min)


def build_appeal_scores(
    database_path: str,
    hit_percentile: float = 0.97,
    x_popularity: float = 1.0,
    y_followers: float = 1.0,
    z_hits: float = 1.0):
# Builds an appeal score for each artist using popularity, followers, hits, and hit momentums

    conn = sqlite3.connect(database_path)

    artists = pd.read_sql_query("SELECT id, name, artist_popularity, followers FROM artist_data", conn)
    tracks = pd.read_sql_query("SELECT id AS track_id, track_popularity FROM tracks_data", conn)
    mapping = pd.read_sql_query("SELECT track_id, artist_id, release_date FROM albums_data", conn)

    genre_cols = [f"genre_{i}" for i in range(7)]
    artist_genres = pd.read_sql_query(f"SELECT id, {', '.join(genre_cols)} FROM artist_data", conn)

    conn.close()

    # 1. Keep only artists with at least one broad genre
    def has_any_genre(row):
        for col in genre_cols:
            val = row[col]
            if pd.notna(val) and str(val).strip() != "":
                return True
        return False

    valid_artist_ids = artist_genres.loc[artist_genres.apply(has_any_genre, axis=1), "id"]

    artists = artists[artists["id"].isin(valid_artist_ids)].copy()
    mapping = mapping[mapping["artist_id"].isin(valid_artist_ids)].copy()
    track_artist = mapping.merge(tracks, on="track_id", how="left")

    # 2. Remove duplicate artist-track pairs
    track_artist = track_artist.drop_duplicates(subset=["artist_id", "track_id"]).copy()
    track_artist["release_date"] = pd.to_datetime(track_artist["release_date"], utc=True)

    # 3. Define hits = top x% of remaining tracks
    hit_threshold = float(np.quantile(track_artist["track_popularity"], hit_percentile))
    track_artist["is_hit"] = track_artist["track_popularity"] >= hit_threshold
    hit_tracks = track_artist[track_artist["is_hit"]].copy()

    # 4. Momentum relative to latest release date in dataset, Recent hits count more
    reference_date = track_artist["release_date"].max()

    hit_tracks["years_since_release"] = ((reference_date - hit_tracks["release_date"]).dt.days / 365.25)

    hit_tracks["momentum_weight"] = np.exp(-0.15 * hit_tracks["years_since_release"])
    hit_tracks["momentum_adjusted_hit"] = (hit_tracks["track_popularity"] * hit_tracks["momentum_weight"])

    hit_stats = (
        hit_tracks.groupby("artist_id", as_index=False)
        .agg(
            hit_count=("track_id", "count"),
            hit_strength=("track_popularity", "sum"),
            momentum_adjusted_hit_strength=("momentum_adjusted_hit", "sum"),
            newest_hit_release=("release_date", "max")))

    top_track = (track_artist.groupby("artist_id", as_index=False).agg(top_track_popularity=("track_popularity", "max")))


    # Merge to artist table
    df = artists.merge(hit_stats, left_on="id", right_on="artist_id", how="left")
    df = df.merge(top_track, left_on="id", right_on="artist_id", how="left", suffixes=("", "_y"))

    for col in ["artist_id", "artist_id_y"]:
        if col in df.columns:
            df = df.drop(columns=[col])

    # Clean
    df["hit_count"] = df["hit_count"].fillna(0).astype(int)
    df["hit_strength"] = df["hit_strength"].fillna(0.0)
    df["momentum_adjusted_hit_strength"] = df["momentum_adjusted_hit_strength"].fillna(0.0)
    df["top_track_popularity"] =df["top_track_popularity"].fillna(0.0)
    df["newest_hit_release"] = pd.to_datetime(df["newest_hit_release"])

    # Transformations
    followers_log = np.log10(df["followers"] + 1.0)
    momentum_hits_sqrt = np.sqrt(df["momentum_adjusted_hit_strength"])

    # Normalize to 0-100
    df["followers_100"] = _minmax_0_100(pd.Series(followers_log, index=df.index))
    df["momentum_hits_100"] = _minmax_0_100(pd.Series(momentum_hits_sqrt, index=df.index))

    # Final appeal formula
    df["appeal_score"] = (float(x_popularity) * df["artist_popularity"] + float(y_followers) * df["followers_100"] + float(z_hits) * df["momentum_hits_100"])
    df["hit_threshold_track_popularity"] = hit_threshold
    df["reference_release_date"] = reference_date

    return df[[
        "id",
        "name",
        "followers",
        "hit_count",
        "hit_strength",
        "momentum_adjusted_hit_strength",
        "top_track_popularity",
        "newest_hit_release",
        "artist_popularity",
        "followers_100",
        "momentum_hits_100",
        "appeal_score",
        "hit_threshold_track_popularity",
        "reference_release_date"]]

#if __name__ == "__main__":
    result = build_appeal_scores(
        "spotify_database.db",
        hit_percentile=0.99,
        x_popularity=1.0,
        y_followers=1.0,
        z_hits=1.0).sort_values("appeal_score", ascending=False)

    print(
        result[
            [
                "name",
                "artist_popularity",
                "followers_100",
                "hit_count",
                "momentum_adjusted_hit_strength",
                "momentum_hits_100",
                "appeal_score"]].head(100).to_string(index=False)
    )