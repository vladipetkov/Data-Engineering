import pandas as pd
import os
import matplotlib.pyplot as plt
import statsmodels.api as sm
import numpy as np
from difflib import SequenceMatcher

"""
Basic inspection of the data
"""
current_file = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file)
parent_dir = os.path.dirname(current_dir)
print(parent_dir)

file_path = os.path.join(parent_dir, "artist_data.csv")
df = pd.read_csv(file_path)
print("_______________\n")
print(f"There are in total {df['id'].nunique()} different artists in the given data set!")
print("_______________\n")

def select_top_10_artists(df):
    popularity = df.sort_values(by = ["artist_popularity", "followers"], ascending=[False, False]).head(n=10)
    popularity = popularity.reset_index(drop = True)
    return popularity

top_10_whole_df = select_top_10_artists(df)
plt.scatter(top_10_whole_df.loc[range(10), "artist_popularity"], top_10_whole_df.loc[range(10), "followers"]/ 1e6, color = "purple")
plt.xlabel("Popularity Index")
plt.ylabel("Followers in millions")
plt.title("Followers vs Popularity Index per Artist")
plt.show()


"""
Popularity vs followers
"""
print("The correlation between followers and popularity is shown in the table below: \n", 
      df[["followers","artist_popularity"]].corr(),
      "\n")
print("_______________\n")
new_df = df[df["followers"] > 0].copy()
new_df["log_followers"] = np.log(new_df["followers"])

print("The correlation between log(followers) and popularity is  shown in the table below: \n", 
      new_df[["log_followers","artist_popularity"]].corr(),
      "\n")
print("_______________\n")
model = sm.formula.ols(
    formula="artist_popularity ~ log_followers",
    data=new_df
)
results = model.fit()

print(results.summary())
print("_______________\n")

intercept = results.params['Intercept']
slope_log_followers = results.params['log_followers']

new_df.sample(150).plot.scatter("log_followers","artist_popularity")
plt.axline((0,intercept), slope = slope_log_followers, color = "r")
plt.show()

print("5 artists with low popularity but high followers: \n",
      df[df["artist_popularity"] < 51].sort_values(by="followers", ascending = False).loc[:,["id","artist_popularity","artist_genres","followers" ]].head())
print("_______________\n")
print("5 artists with high popularity but low followers: \n",
       df[df["artist_popularity"] > 70].sort_values(by="followers", ascending = True).loc[:,["id","artist_popularity","artist_genres","followers" ]].head())
print("_______________\n")

"""
Relevance of genres Part 1
"""
def top_10_per_genre(genre, df, plain_genre): #parameter plain_genre is of type bool. If true, the function looks for exact gengre, if false, it looks for all genres containing the given one; for example "canadian pop" includes "pop", but not the oposite
    if plain_genre:
        filtered_df_genre = df[ (df["genre_0"] == genre) |
                                (df["genre_1"] == genre) |
                                (df["genre_2"] == genre) |
                                (df["genre_3"] == genre) |
                                (df["genre_4"] == genre) |
                                (df["genre_5"] == genre) |
                                (df["genre_6"] == genre) ]
        
        top_10_artists_genre_df = select_top_10_artists(filtered_df_genre)
        return top_10_artists_genre_df.loc[:,["id","artist_popularity","artist_genres","followers" ]]
    else:
        filtered_df_genre = df[ (df["genre_0"].str.contains(genre, na=False)) |
                                (df["genre_1"].str.contains(genre, na=False)) |
                                (df["genre_2"].str.contains(genre, na=False)) |
                                (df["genre_3"].str.contains(genre, na=False)) |
                                (df["genre_4"].str.contains(genre, na=False))]
        
        top_10_artists_genre_df = select_top_10_artists(filtered_df_genre)
        return top_10_artists_genre_df.loc[:,["id","artist_popularity","artist_genres","followers" ]]
    
print("The top 10 artists in pop are: \n",
      top_10_per_genre("pop", df, False), 
      "\n")
print("_______________\n")

"""
Relevance of genres Part 2
"""
def genre_count(df):
    genre_column=[]
    for column in df.columns:
        if column.startswith("genre_"):
            genre_column.append(column)

    df["numb_genres"] = 0
    for i in range(len(df)):
        count = 0
        for col in genre_column:
            value=df.loc[i, col]
            if not pd.isna(value):
                count+=1
        df.loc[i,"numb_genres"] = count

    print("The total number of genres per artis is estimated to be as follows: \n")
    genres_conted_per_artist = df["numb_genres"].value_counts().sort_index()
    for genre in range(len(genres_conted_per_artist)):
        print(f"Artists with {genre+1} genres are in total {genres_conted_per_artist.iloc[genre]}.")
    
    print("_______________\n")

    print("A statistical summary of the number of genres is provided below: \n", 
          df["numb_genres"].describe(),
          "\n")
    print("_______________\n")

    #“Correlation on the raw scale gets distorted. Fix: use log scale for 1 + x, so x=0 does not cause an issue too. Try correlating popularity with log_followers."
    df["log_followers"] = np.log1p(df["followers"]) 
    corr_matrix = df[["numb_genres", "artist_popularity", "log_followers"]].corr()
    print("Correlation matrix is presented below: \n",corr_matrix)

    #Histogram
    plt.figure()
    plt.hist(df["numb_genres"], range(0, int(df["numb_genres"].max()) + 1))
    plt.xlabel("Number of Genres per Artist")
    plt.ylabel("Number of Artists")
    plt.title("Distribution of Number of Genres per Artist")
    plt.show()

    # Boxplot Popularity
    boxplot_popularity_genres = df.boxplot("artist_popularity", "numb_genres")
    boxplot_popularity_genres.set_xlabel("Number of Genres")
    boxplot_popularity_genres.set_ylabel("Artist Popularity")
    boxplot_popularity_genres.set_title("Popularity Distribution by Number of Genres")

    plt.suptitle("")
    plt.show()

    #Boxplot Log Followers
    boxplot_followers_genres = df.boxplot("log_followers", "numb_genres")
    boxplot_followers_genres.set_xlabel("Number of Genres")
    boxplot_followers_genres.set_ylabel("Log(Followers)")
    boxplot_followers_genres.set_title("Log(Followers) Distribution by Number of Genres")

    plt.suptitle("")
    plt.show()

    #Mean Popularity Line Plot
    mean_popularity = df.groupby("numb_genres")["artist_popularity"].mean()
    plt.figure()
    mean_popularity.plot()
    plt.xlabel("Number of Genres")
    plt.ylabel("Average Popularity")
    plt.title("Average Popularity by Number of Genres")
    plt.show()

genre_count(df)

"""
name association

we were curious as to see if the top 10 artists have other artists with close names and what would the popularity and followers comparison be like; 
the followers one had a lot of outliers and was difficult to visualise well, so we decided not to include it
"""

shortened_df = df[["name", "artist_popularity", "followers"]].copy()
shortened_df = shortened_df.assign(name_stripped = None, closest_artist = None, similarity_score = None)

for artist in range(len(shortened_df)):
    stripped_name = "".join(shortened_df.loc[artist, "name"].lower().split())
    shortened_df.loc[artist, "name_stripped"] = stripped_name

top_10_artists_stripped = []
for artist in range(len(select_top_10_artists(shortened_df))):
    top_10_artists_stripped.append(select_top_10_artists(shortened_df).loc[artist, "name_stripped"])

def similarity_check(artist_index_row, df, threshold=0.65): #0.65 was determined best by manual adjustment
    name = df.loc[artist_index_row, "name_stripped"]
    closest_artist = None
    best_similarity_score = 0

    for artist in top_10_artists_stripped:
        if SequenceMatcher(None, name, artist).ratio() > best_similarity_score:
            best_similarity_score = SequenceMatcher(None, name, artist).ratio()
            closest_artist = artist

    if best_similarity_score == 1:
        return #we want not to include the top 10 in the match-making
    
    if best_similarity_score > threshold:
        df.loc[artist_index_row, "closest_artist"] = closest_artist
        df.loc[artist_index_row, "similarity_score"] = best_similarity_score
        return True
    return False

similarities = {artist: [] for artist in top_10_artists_stripped}

for artist in range(len(shortened_df)):
    if similarity_check(artist, shortened_df):
        similarities[shortened_df.loc[artist, "closest_artist"]].append(artist)

popularity_data = []
for artist, list in similarities.items():
    print(f"{artist} has {len(list)} similar artists: \n")

    current_list = []
    for item in range(len(list)):
        print(shortened_df.loc[list[item], "name"])
        current_list.append(shortened_df.loc[list[item], "artist_popularity"])
    popularity_data.append(current_list)
    print("_________")

plt.boxplot(popularity_data, tick_labels = top_10_artists_stripped)
plt.xlabel("Artist")
plt.ylabel("Popularity Score")
plt.title("Popularity of the Top 10 Artists' Similar Artists")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()