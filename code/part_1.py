import pandas as pd
import os
import matplotlib.pyplot as plt
import statsmodels.api as sm
import numpy as np

"""
Basic inspection of the data
"""
current_file = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file)
parent_dir = os.path.dirname(current_dir)
print(parent_dir)

file_path = os.path.join(parent_dir, "artist_data.csv")
df = pd.read_csv(file_path)
# print(df["id"].nunique())

def select_top_10_artists(df):
    popularity = df.sort_values(by = ["artist_popularity", "followers"], ascending=[False, False]).head(n=10)
    popularity = popularity.reset_index(drop = True)
    return popularity

# top_10_whole_df = select_top_10_artists(df)
# plt.scatter(top_10_whole_df.loc[range(10), "artist_popularity"], top_10_whole_df.loc[range(10), "followers"]/ 1e6, color = "purple")
# plt.xlabel("Popularity Index")
# plt.ylabel("Followers in millions")
# plt.title("Followers vs Popularity Index per Artist")
# plt.show()


"""
Popularity vs followers
"""
print("The correlation between followers and popularity is: ", df[["followers","artist_popularity"]].corr())

new_df = df[df["followers"] > 0]
new_df["log_followers"] = np.log(new_df["followers"])

print("The correlation between log(followers) and popularity is: ", new_df[["log_followers","artist_popularity"]].corr())

model = sm.formula.ols(
    formula="artist_popularity ~ log_followers",
    data=new_df
)
results = model.fit()

print(results.summary())

intercept = results.params['Intercept']
slope_log_followers = results.params['log_followers']

new_df.sample(150).plot.scatter("log_followers","artist_popularity")
plt.axline((0,intercept), slope = slope_log_followers, color = "r")
plt.show()

print("5 artists with low popularity but high followers:")
print(df[df["artist_popularity"] < 51].sort_values(by="followers", ascending = False).head())

print("5 artists with high popularity but low followers:")
print(df[df["artist_popularity"] > 70].sort_values(by="followers", ascending = True).head())


"""
Relevance of genres Part 1
"""
def top_10_per_genre(genre, df, plain_genre):
    if plain_genre:
        filtered_df_genre = df[ (df["genre_0"] == genre) |
                                (df["genre_1"] == genre) |
                                (df["genre_2"] == genre) |
                                (df["genre_3"] == genre) |
                                (df["genre_4"] == genre) |
                                (df["genre_5"] == genre) |
                                (df["genre_6"] == genre) ]
        
        top_10_artists_genre_df = select_top_10_artists(filtered_df_genre)
        return top_10_artists_genre_df
    else:
        filtered_df_genre = df[ (df["genre_0"].str.contains(genre, na=False)) |
                                (df["genre_1"].str.contains(genre, na=False)) |
                                (df["genre_2"].str.contains(genre, na=False)) |
                                (df["genre_3"].str.contains(genre, na=False)) |
                                (df["genre_4"].str.contains(genre, na=False))]
        
        top_10_artists_genre_df = select_top_10_artists(filtered_df_genre)
        return top_10_artists_genre_df

print(top_10_per_genre("pop", df, False))
# print(df.loc[0,"genre_5"])


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

    basic_summary=df["numb_genres"].value_counts().sort_index()
    descriptive_stats = df["numb_genres"].describe()
    #“Correlation on the raw scale gets distorted. Fix: use log scale Try correlating popularity with log_followers."
    df["log_followers"] = np.log(df["followers"])
    corr_matrix = df[["numb_genres", "artist_popularity", "log_followers"]].corr()

    #Histogram
    plt.figure()
    plt.hist(df["numb_genres"], range(0, int(df["numb_genres"].max()) + 1))
    plt.xlabel("Number of Genres per Artist")
    plt.ylabel("Number of Artists")
    plt.title("Distribution of Number of Genres per Artist")
    plt.show()

    #Boxplot Popularity
    plt.figure()
    df.boxplot("artist_popularity", "numb_genres")
    plt.xlabel("Number of Genres")
    plt.ylabel("Artist Popularity")
    plt.title("Popularity Distribution by Number of Genres")
    plt.show()

    #Boxplot Log Followers
    plt.figure()
    df.boxplot("log_followers", "numb_genres")
    plt.xlabel("Number of Genres")
    plt.ylabel("Log(Followers)")
    plt.title("Log(Followers) Distribution by Number of Genres")
    plt.show()

    #Mean Popularity Line Plot
    mean_popularity = df.groupby("numb_genres")["artist_popularity"].mean()
    plt.figure()
    mean_popularity.plot()
    plt.xlabel("Number of Genres")
    plt.ylabel("Average Popularity")
    plt.title("Average Popularity by Number of Genres")
    plt.show()

    return basic_summary, descriptive_stats, corr_matrix

print(genre_count(df))