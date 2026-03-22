import pandas as pd
import plotly.express as px
import streamlit as st
import sqlite3
import io

from .stage import BROAD_GENRES, make_genre_stage, make_main_stage, make_multi_genre_stage
from .optimization import FestivalInputs, optimize_festival_lineup

NEW_THEME = {
    "bg": "#ff2f5f",
    "paper": "#ff2f5f",
    "card": "#f2b5df",
    "ink": "#ffffff",
    "ink_dark": "#163ea8",
    "yellow": "#f7e53b",
    "blue": "#1f58c7",
    "pink": "#ff2f5f",
    "lavender": "#c98cc2",
    "magenta": "#ef336a",
}

NEW_PALETTE = [
    NEW_THEME["yellow"],
    NEW_THEME["blue"],
    "#d7a5cc",
    "#f1cf69",
    "#7bc7ff",
    "#ef9cc5",
    "#8e68c9",
    "#e9e9e9",
]


def fmt_money(x):
    return f"${float(x):,.0f}"


def fmt_num(x, digits=1):
    return f"{float(x):,.{digits}f}"


def _fmt_millions_3(x):
    return f"{float(x) / 1_000_000:.3f}M"



def apply_new_layout(fig, xaxis_title="", yaxis_title="", show_legend=True, pie_chart=False):
    fig.update_layout(
        title=None,
        title_text="",
        paper_bgcolor=NEW_THEME["paper"],
        plot_bgcolor=NEW_THEME["card"] if not pie_chart else NEW_THEME["paper"],
        font=dict(color=NEW_THEME["ink"], size=14),
        legend=dict(
            title_text="",
            title_font=dict(color=NEW_THEME["ink"]),
            font=dict(color=NEW_THEME["ink"]),
            bgcolor="rgba(0,0,0,0)",
            orientation="v" if pie_chart else "h",
            yanchor="top" if pie_chart else "bottom",
            y=1.0 if pie_chart else 1.02,
            xanchor="left" if pie_chart else "right",
            x=1.02 if pie_chart else 1,
        ),
        margin=dict(l=20, r=20 if not pie_chart else 140, t=20, b=20),
        showlegend=show_legend,
        uniformtext_minsize=8,
        uniformtext_mode="hide",
    )
    fig.update_xaxes(
        title=xaxis_title,
        showgrid=False,
        zeroline=False,
        linecolor=NEW_THEME["ink"],
        tickfont=dict(color=NEW_THEME["ink"]),
        title_font=dict(color=NEW_THEME["yellow"]),
    )
    fig.update_yaxes(
        title=yaxis_title,
        gridcolor="rgba(255,255,255,0.18)",
        zeroline=False,
        linecolor=NEW_THEME["ink"],
        tickfont=dict(color=NEW_THEME["ink"]),
        title_font=dict(color=NEW_THEME["yellow"]),
    )
    return fig


def ensure_stage_defaults(session_state, n_stages: int):
    for i in range(n_stages):
        if f"stage_name_{i}" not in session_state:
            session_state[f"stage_name_{i}"] = f"Stage {i+1}"
        if f"stage_type_{i}" not in session_state:
            session_state[f"stage_type_{i}"] = "Main" if i == 0 else "Single Genre"
        if f"stage_budget_{i}" not in session_state:
            session_state[f"stage_budget_{i}"] = 5_000_000.0
        if f"stage_genre_{i}" not in session_state:
            session_state[f"stage_genre_{i}"] = "Hip-Hop"
        if f"stage_genres_{i}" not in session_state:
            session_state[f"stage_genres_{i}"] = ["Electronic Dance Music (EDM)", "Rock"]


def build_stage_objects(session_state, n_stages: int):
    stages = []
    for i in range(n_stages):
        stage_name = session_state.get(f"stage_name_{i}", f"Stage {i+1}")
        stage_type = session_state.get(f"stage_type_{i}", "Single Genre")
        stage_budget = float(session_state.get(f"stage_budget_{i}", 10_000_000.0))

        if stage_type == "Main":
            stage_obj = make_main_stage(stage_name, stage_budget)
        elif stage_type == "Single Genre":
            genre = session_state.get(f"stage_genre_{i}", "Hip-Hop")
            stage_obj = make_genre_stage(stage_name, stage_budget, genre)
        else:
            genres = session_state.get(f"stage_genres_{i}", ["Electronic Dance Music (EDM)", "Rock"])
            if not genres:
                genres = ["Electronic Dance Music (EDM)", "Rock"]
            stage_obj = make_multi_genre_stage(stage_name, stage_budget, set(genres))
        stages.append(stage_obj)

    return stages


def lineup_stage_filter(df: pd.DataFrame, selected_stage: str):
    if selected_stage == "All stages":
        return df.copy()
    return df[df["stage"] == selected_stage].copy()


def prepare_lineup_table(df: pd.DataFrame):
    out = df.copy()
    out["Genres"] = out["broad_genres"].apply(lambda x: ", ".join(x) if isinstance(x, list) and len(x) > 0 else "-")
    out = out.rename(
        columns={
            "stage": "Stage",
            "artist_name": "Artist",
            "appeal_score": "Appeal",
            "cost_of_artist": "Cost",
        }
    )
    out["Cost"] = out["Cost"].apply(fmt_money)
    out["Appeal"] = out["Appeal"].apply(lambda x: fmt_num(x, 1))
    return out[["Stage", "Artist", "Appeal", "Cost", "Genres"]]


def prepare_budget_table(df: pd.DataFrame):
    out = df.copy()
    out = out.rename(
        columns={
            "stage": "Stage",
            "stage_budget": "Stage Budget",
            "total_cost": "Total Cost",
            "remaining_budget": "Remaining Budget",
            "total_appeal": "Total Appeal",
        }
    )
    out["Stage Budget"] = out["Stage Budget"].apply(fmt_money)
    out["Total Cost"] = out["Total Cost"].apply(fmt_money)
    out["Remaining Budget"] = out["Remaining Budget"].apply(fmt_money)
    out["Total Appeal"] = out["Total Appeal"].apply(lambda x: fmt_num(x, 1))
    return out


def make_budget_chart(budget_df: pd.DataFrame):
    plot_df = budget_df[["stage", "stage_budget", "total_cost"]].copy()
    plot_df = plot_df.melt(
        id_vars="stage",
        value_vars=["stage_budget", "total_cost"],
        var_name="Measure",
        value_name="Value",
    )
    plot_df["Label"] = plot_df["Value"].apply(_fmt_millions_3)

    fig = px.bar(
        plot_df,
        x="stage",
        y="Value",
        color="Measure",
        barmode="group",
        color_discrete_map={
            "stage_budget": NEW_THEME["yellow"],
            "total_cost": NEW_THEME["blue"],
        },
        text="Label",
    )
    fig.update_traces(
        marker_line_color=NEW_THEME["ink"],
        marker_line_width=2,
        textposition="outside",
        textfont=dict(color=NEW_THEME["ink"], size=13),
        cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>%{fullData.name}: %{y:,.3f}<extra></extra>",
    )
    fig.update_yaxes(tickformat=",.3f")
    fig.update_layout(title=None, title_text="")
    return apply_new_layout(fig, "Stage", "Amount")


def make_appeal_chart(budget_df: pd.DataFrame):
    plot_df = budget_df.copy()
    plot_df["Label"] = plot_df["total_appeal"].apply(lambda x: fmt_num(x, 1))

    fig = px.bar(
        plot_df,
        x="stage",
        y="total_appeal",
        color_discrete_sequence=[NEW_THEME["yellow"]],
        text="Label",
    )
    fig.update_traces(
        marker_line_color=NEW_THEME["ink"],
        marker_line_width=2,
        textposition="outside",
        textfont=dict(color=NEW_THEME["ink"], size=13),
        cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Total Appeal: %{y:,.3f}<extra></extra>",
    )
    fig.update_layout(title=None, title_text="")
    return apply_new_layout(fig, "Stage", "Total Appeal", show_legend=False)


def make_genre_chart(genre_df: pd.DataFrame):
    fig = px.bar(
        genre_df,
        x="Genre",
        y="Count",
        color="Genre",
        color_discrete_sequence=NEW_PALETTE,
        text="Count",
    )
    fig.update_traces(
        marker_line_color=NEW_THEME["ink"],
        marker_line_width=2,
        textposition="outside",
        cliponaxis=False,
    )
    fig.update_layout(title=None, title_text="")
    return apply_new_layout(fig, "Genre", "Count")


def run_festival_model(session_state, database_path: str, n_stages: int, n_days: int, performances_per_day_per_stage: int, total_budget: float, hit_percentile: float, objective: str = "max_appeal"):
    stages = build_stage_objects(session_state, n_stages)
    inputs = FestivalInputs(
        database_path=database_path,
        n_days=n_days,
        performances_per_day_per_stage=performances_per_day_per_stage,
        stages=stages,
        total_budget=float(total_budget),
        hit_percentile=float(hit_percentile),
        objective=objective,
    )

    result = optimize_festival_lineup(inputs)
    lineup = result.get("lineup", pd.DataFrame())
    budget = result.get("budget", pd.DataFrame())
    solver_status = result.get("solver_status", "-")
    genre_distribution = build_genre_distribution(lineup)

    total_cost = float(budget["total_cost"].sum())
    total_appeal = float(budget["total_appeal"].sum())
    selected_artists = len(lineup)

    return {
        "raw_result": result,
        "lineup": lineup,
        "budget": budget,
        "solver_status": solver_status,
        "genre_distribution": genre_distribution,
        "total_cost": total_cost,
        "total_appeal": total_appeal,
        "selected_artists": selected_artists,
        "objective": objective,
    }


def build_genre_distribution(lineup_df: pd.DataFrame):
    exploded = lineup_df[["broad_genres"]].explode("broad_genres")
    exploded = exploded.dropna(subset=["broad_genres"])
    out = exploded["broad_genres"].value_counts().reset_index()
    out.columns = ["Genre", "Count"]
    return out


def make_genre_pie_chart(genre_df: pd.DataFrame):
    fig = px.pie(
        genre_df,
        names="Genre",
        values="Count",
        color="Genre",
        color_discrete_sequence=NEW_PALETTE,
    )
    fig.update_traces(
        hole=0,
        pull=[0] * len(genre_df),
        textfont=dict(color=NEW_THEME["ink"], size=13),
        marker=dict(line=dict(color=NEW_THEME["paper"], width=0)),
        textinfo="percent",
        texttemplate="%{percent:.1%}",
        sort=False,
        direction="clockwise",
        hovertemplate="Genre=%{label}<br>Count=%{value}<extra></extra>",
    )
    fig.update_layout(title=None, title_text="")
    return apply_new_layout(fig, show_legend=True, pie_chart=True)


def get_artists_by_genre(lineup_df: pd.DataFrame, selected_genre: str):
    filtered = lineup_df[
        lineup_df["broad_genres"].apply(lambda genres: selected_genre in genres if isinstance(genres, list) else False)
    ].copy()
    filtered = filtered.rename(
        columns={
            "artist_name": "Artist",
            "stage": "Stage",
            "appeal_score": "Appeal",
            "cost_of_artist": "Cost",
        }
    )
    return filtered[["Artist", "Stage", "Appeal", "Cost"]].sort_values("Appeal", ascending=False)


def build_lineup_release_data(lineup_df: pd.DataFrame, database_path: str):
    conn = sqlite3.connect(database_path)
    albums = pd.read_sql_query("SELECT artist_id, release_date FROM albums_data", conn)
    conn.close()

    albums["artist_id"] = albums["artist_id"].astype(str)
    albums["release_date"] = pd.to_datetime(albums["release_date"], errors="coerce")
    albums["release_year"] = albums["release_date"].dt.year
    albums = albums.copy()
    albums["release_year"] = albums["release_year"].astype(int)
    albums = albums[(albums["release_year"] >= 1940) & (albums["release_year"] < 2030)].copy()

    lineup_artists = lineup_df[["artist_id", "artist_name", "broad_genres"]].copy()
    lineup_artists["artist_id"] = lineup_artists["artist_id"].astype(str)

    merged = lineup_artists.merge(albums[["artist_id", "release_date", "release_year"]], on="artist_id", how="left")
    merged = merged.dropna(subset=["release_year"]).copy()
    merged["release_year"] = merged["release_year"].astype(int)
    merged["decade_label"] = (merged["release_year"] // 10 * 10).astype(str) + "s"
    return merged


DECADE_ORDER = ["1940s", "1950s", "1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]


def build_decade_genre_album_counts(release_df: pd.DataFrame):
    out = release_df[["decade_label", "broad_genres"]].copy()
    out = out.explode("broad_genres")
    out = out.dropna(subset=["broad_genres"])
    out = out.rename(columns={"decade_label": "Decade", "broad_genres": "Genre"})
    out["Album Count"] = 1
    out = out.groupby(["Decade", "Genre"], as_index=False)["Album Count"].sum()
    out["Decade"] = pd.Categorical(out["Decade"], categories=DECADE_ORDER, ordered=True)
    out = out.sort_values(["Decade", "Genre"]).reset_index(drop=True)
    return out


def make_decade_genre_album_area_chart(decade_genre_df: pd.DataFrame):
    fig = px.area(
        decade_genre_df,
        x="Decade",
        y="Album Count",
        color="Genre",
        category_orders={"Decade": DECADE_ORDER},
        color_discrete_sequence=NEW_PALETTE,
    )
    fig.update_traces(line=dict(width=2))
    fig.update_xaxes(categoryorder="array", categoryarray=DECADE_ORDER)
    fig.update_layout(title=None, title_text="")
    return apply_new_layout(fig, "Decade", "Number of albums")


def make_release_year_boxplot(release_df: pd.DataFrame):
    fig = px.box(
        release_df,
        y="release_year",
        points="outliers",
        color_discrete_sequence=[NEW_THEME["yellow"]],
    )
    fig.update_traces(
        marker=dict(color=NEW_THEME["blue"], size=8, line=dict(color=NEW_THEME["ink"], width=1)),
        line=dict(color=NEW_THEME["ink"], width=3),
        fillcolor=NEW_THEME["yellow"],
        hovertemplate="Release year: %{y}<extra></extra>",
    )
    fig.update_yaxes(categoryorder="array", categoryarray=DECADE_ORDER)
    fig.update_layout(title=None, title_text="")
    return apply_new_layout(fig, "", "Album release year", show_legend=False)


def build_release_summary(release_df: pd.DataFrame):
    avg_year = release_df["release_year"].mean()
    med_year = release_df["release_year"].median()
    oldest_year = int(release_df["release_year"].min())
    newest_year = int(release_df["release_year"].max())

    oldest_albums = sorted(release_df.loc[release_df["release_year"] == oldest_year, "artist_name"].dropna().unique().tolist())
    newest_albums = sorted(release_df.loc[release_df["release_year"] == newest_year, "artist_name"].dropna().unique().tolist())

    return {
        "average_release_year": avg_year,
        "median_release_year": med_year,
        "oldest_year": oldest_year,
        "oldest_albums": oldest_albums,
        "newest_year": newest_year,
        "newest_albums": newest_albums,
    }


def extract_solution_metrics(result_dict: dict):
    return {
        "Total Cost": result_dict["total_cost"],
        "Total Appeal": result_dict["total_appeal"],
        "Selected Artists": result_dict["selected_artists"],
    }


def render_solution_comparison_block(result_dict: dict, title: str, key_suffix: str):
    if result_dict is None:
        st.info("No solution available.")
        return

    lineup = result_dict["lineup"]
    budget = result_dict["budget"]
    genre_distribution = result_dict["genre_distribution"]
    total_cost = result_dict["total_cost"]
    total_appeal = result_dict["total_appeal"]
    selected_artists = result_dict["selected_artists"]

    st.subheader(title)
    k1, k2, k3 = st.columns(3)
    k1.metric("Total cost", fmt_money(total_cost))
    k2.metric("Total appeal", fmt_num(total_appeal, 1))
    k3.metric("Selected artists", selected_artists)

    st.subheader("Budget summary")
    st.dataframe(prepare_budget_table(budget), use_container_width=True, hide_index=True)

    st.subheader("Lineup")
    stage_options = ["All stages"]
    if "stage" in lineup.columns:
        stage_options += sorted(lineup["stage"].dropna().unique().tolist())
    selected_stage = st.selectbox("Show lineup for stage", options=stage_options, key=f"stage_select_{key_suffix}")

    filtered_lineup = lineup_stage_filter(lineup, selected_stage)
    st.dataframe(prepare_lineup_table(filtered_lineup), use_container_width=True, hide_index=True)

    st.subheader("Budget vs Cost by stage")
    st.plotly_chart(make_budget_chart(budget), use_container_width=True, key=f"budget_chart_{key_suffix}")

    st.subheader("Genre distribution")
    st.plotly_chart(make_genre_pie_chart(genre_distribution), use_container_width=True, key=f"genre_chart_{key_suffix}")

    genre_options = genre_distribution["Genre"].tolist()
    selected_genre = st.selectbox("Select genre", options=genre_options, key=f"genre_select_{key_suffix}")
    genre_artist_table = get_artists_by_genre(lineup, selected_genre)
    genre_artist_table["Appeal"] = genre_artist_table["Appeal"].apply(lambda x: fmt_num(x, 1))
    genre_artist_table["Cost"] = genre_artist_table["Cost"].apply(fmt_money)
    st.dataframe(genre_artist_table, use_container_width=True, hide_index=True)


def build_solution_comparison(best_result: dict, worst_result: dict):
    best_metrics = extract_solution_metrics(best_result)
    worst_metrics = extract_solution_metrics(worst_result)
    df = pd.DataFrame([
        {"Scenario": "Best Solution (Max Appeal)", **best_metrics},
        {"Scenario": "Worst Solution (Min Appeal)", **worst_metrics},
    ])
    return df


def make_appeal_comparison_chart(best_budget_df: pd.DataFrame, worst_budget_df: pd.DataFrame):
    best_result_appeal_per_stage = best_budget_df[["stage", "total_appeal"]].copy()
    best_result_appeal_per_stage["Measure"] = "Best solution (Max Appeal)"
    worst_result_appeal_per_stage = worst_budget_df[["stage", "total_appeal"]].copy()
    worst_result_appeal_per_stage["Measure"] = "Worst solution (Min Appeal)"
    plot_df = pd.concat([best_result_appeal_per_stage, worst_result_appeal_per_stage], ignore_index=True)
    plot_df["Label"] = plot_df["total_appeal"].apply(lambda x: fmt_num(x, 1))

    fig = px.bar(
        plot_df,
        x="stage",
        y="total_appeal",
        color="Measure",
        barmode="group",
        color_discrete_map={
            "Best solution (Max Appeal)": NEW_THEME["yellow"],
            "Worst solution (Min Appeal)": NEW_THEME["blue"],
        },
        text="Label",
    )
    fig.update_traces(
        marker_line_color=NEW_THEME["ink"],
        marker_line_width=2,
        textposition="outside",
        textfont=dict(color=NEW_THEME["ink"], size=13),
        cliponaxis=False,
    )
    fig.update_layout(title=None, title_text="")
    return apply_new_layout(fig, "Stage", "Total Appeal")

def build_excel_file(result_dict, festival_name):
    output = io.BytesIO()
    raw_result = result_dict["raw_result"]
    lineup = result_dict["lineup"].copy()
    budget = result_dict["budget"].copy()
    genre_distribution = result_dict["genre_distribution"].copy()
    master = raw_result.get("master", pd.DataFrame()).copy()
    wide = raw_result.get("wide", pd.DataFrame()).copy()

    summary_df = pd.DataFrame([
        {
            "Festival Name": festival_name,
            "Objective": result_dict["objective"],
            "Total Cost": result_dict["total_cost"],
            "Total Appeal": result_dict["total_appeal"],
            "Selected Artists": result_dict["selected_artists"]}
    ])

    if "broad_genres" in lineup.columns:
        lineup["broad_genres"] = lineup["broad_genres"].apply(lambda x: ", ".join(x) if isinstance(x, list) else "")

    if "broad_genres" in master.columns:
        master["broad_genres"] = master["broad_genres"].apply(lambda x: ", ".join(x) if isinstance(x, list) else "")

    if "broad_genres" in wide.columns:
        wide["broad_genres"] = wide["broad_genres"].apply(lambda x: ", ".join(x) if isinstance(x, list) else "")

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary_df.to_excel(writer, index=False, sheet_name="Summary")
        lineup.to_excel(writer, index=False, sheet_name="Lineup")
        budget.to_excel(writer, index=False, sheet_name="Budget")
        genre_distribution.to_excel(writer, index=False, sheet_name="Genre Distribution")
        master.to_excel(writer, index=False, sheet_name="Master Artist Table")
        wide.to_excel(writer, index=False, sheet_name="Stage Eligibility")

    output.seek(0)
    return output.getvalue()