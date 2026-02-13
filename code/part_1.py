import pandas as pd
from matplotlib import pyplot as plt
import statsmodels.api as sm
import numpy as np

df = pd.read_csv("artist_data.csv")

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