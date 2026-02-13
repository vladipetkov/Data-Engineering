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
Relevance of genres
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