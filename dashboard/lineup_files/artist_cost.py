import sqlite3
import pandas as pd
import numpy as np

def tiered_price(s):
    #0-0.3 1k to 10k
    if s <= 0.3:
        t = s/0.3
        return 1000*(10000/1000)**t
    #0.3 -0.7 10k to 500k
    elif s <= 0.7:
        t = (s-0.3) /0.4
        return 10000*(500000/10000)**t

    #0.7-0.9 500k to 1M
    elif s <= 0.9:
        t = (s-0.7)/0.2
        return 500000*(1000000/500000)**t

    #0.9-0.95 1M to 3M
    elif s <= 0.95:
        t = (s - 0.9)/0.05
        return 1000000*(3000000/1000000)**t

        # 0.95 - 1 3M to 10M
    else:
        t = (s-0.95)/0.05
        return 3000000*(10000000/3000000)**t

def calculate_artist_cost(database_path):
    con = sqlite3.connect(database_path)
    df = pd.read_sql_query("SELECT id, name, artist_popularity, followers FROM artist_data",con)
    con.close()

    # Normalize popularity
    df["popularity_norm"] = df["artist_popularity"]/100.0
    # Log-transform followers
    df["followers_log"] = np.log10(df["followers"] +1)

    # Normalize followers_log to 0-1
    min_f = df["followers_log"].min()
    max_f = df["followers_log"].max()
    df["followers_norm"] = (df["followers_log"]-min_f)/(max_f-min_f)

    df["star_score"] = 0.6*df["popularity_norm"]+0.4*df["followers_norm"]

    df["cost_of_artist"] = df["star_score"].apply(tiered_price)
    return df[["id", "name", "artist_popularity", "followers", "cost_of_artist"]]