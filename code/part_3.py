import sqlite3
<<<<<<< Updated upstream
=======
import pandas as pd
import matplotlib.pyplot as plt
import part_3_functions as func
>>>>>>> Stashed changes

con = sqlite3.connect("spotify_database.db")
cur = con.cursor()

<<<<<<< Updated upstream
=======
cur.execute("PRAGMA table_info('features_data');")
columns = cur.fetchall()
for column in columns:
    print(column[1])

func.album_summary('Jar Of Flies',cur)
>>>>>>> Stashed changes
