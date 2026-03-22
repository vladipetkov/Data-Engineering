import streamlit as st
from stage import BROAD_GENRES
from original_festival_analytics import (
    ensure_stage_defaults,
    fmt_money,
    fmt_num,
    lineup_stage_filter,
    make_appeal_chart,
    make_budget_chart,
    make_genre_pie_chart,
    prepare_budget_table,
    prepare_lineup_table,
    run_festival_model,
    get_artists_by_genre,
    build_lineup_release_data,
    build_decade_genre_album_counts,
    make_decade_genre_album_area_chart,
    make_release_year_boxplot,
    build_release_summary,
    build_solution_comparison,
    render_solution_comparison_block,
    make_appeal_comparison_chart
)

DATABASE_PATH = "spotify_database.db"
st.set_page_config(page_title="Festival Dashboard", layout="wide")
st.title("Festival Optimization Dashboard")

col1, col2, col3,col4,col5 = st.columns(5)

with col1:
    st.subheader("**Appeal score**")
    sub1, sub2, sub3 = st.columns(3)
    with sub2: st.image("stars.png", width=100)
    st.caption("Based on popularity, followers, and number of hits (newer the hit is the more it counts, giving it a momentum).")

with col3:
    st.subheader("**Cost estimation**")
    sub1, sub2, sub3 = st.columns(3)
    with sub2: st.image("pricetag.png", width=100)
    st.caption("Estimated booking cost based on popularity and fan base.")

with col5:
    st.subheader("**Genre classification**")
    sub1, sub2, sub3 = st.columns(3)
    with sub2: st.image("genre.png", width=100)
    st.caption("Artists grouped into broad genres using keywords.")

col1, col2, col3,col4,col5 = st.columns(5)

with col2:
    st.subheader("**Stage requirements**")
    sub1, sub2, sub3 = st.columns(3)
    with sub2: st.image("stage.png", width=100)
    st.caption("Assigns artists to stages based on genre and budget.")

with col4:
    st.subheader("**Optimization**")
    sub1, sub2, sub3 = st.columns(3)
    with sub2: st.image("optimization.png", width=100)
    st.caption("Maximizes total appeal under budget and stage constraints.")

# Defaults
st.session_state.setdefault("festival_name", "My Festival")
st.session_state.setdefault("n_stages", 3)
st.session_state.setdefault("n_days", 4)
st.session_state.setdefault("performances_per_day_per_stage", 4)
st.session_state.setdefault("hit_percentile", 0.97)

ensure_stage_defaults(st.session_state, int(st.session_state["n_stages"]))

# Inputs
st.sidebar.header("Inputs")

festival_name = st.sidebar.text_input("Festival name", value=st.session_state["festival_name"])
n_stages = st.sidebar.number_input("Number of stages", min_value=1, max_value=8, value=st.session_state["n_stages"], step=1)
n_days = st.sidebar.number_input("Number of festival days", min_value=1, max_value=14, value=st.session_state["n_days"], step=1)
performances_per_day_per_stage = st.sidebar.number_input(
    "Performances per day per stage",
    min_value=1,
    max_value=12,
    value=st.session_state["performances_per_day_per_stage"],
    step=1)
hit_percentile = st.sidebar.slider(
    "Hit song threshold",
    min_value=0.00,
    max_value=0.99,
    value=float(st.session_state["hit_percentile"]),
    step=0.01)
st.sidebar.caption("Defines how popular a song must be to count as a 'hit'. Higher values mean only top songs contribute to artist appeal.")

n_stages = int(n_stages)
n_days = int(n_days)
performances_per_day_per_stage = int(performances_per_day_per_stage)

ensure_stage_defaults(st.session_state, n_stages)

st.sidebar.subheader("Stage setup")

for i in range(n_stages):
    st.sidebar.markdown(f"**Stage {i+1}**")

    st.session_state[f"stage_name_{i}"] = st.sidebar.text_input(
        f"Stage {i+1} name",
        value=st.session_state.get(f"stage_name_{i}", f"Stage {i+1}"),
        key=f"stage_name_input_{i}")

    default_type = st.session_state.get(f"stage_type_{i}", "Main" if i == 0 else "Single Genre")
    type_options = ["Main", "Single Genre", "Multi Genre"]
    default_index = type_options.index(default_type) if default_type in type_options else 1

    st.session_state[f"stage_type_{i}"] = st.sidebar.selectbox(
        f"Stage {i+1} type",
        options=type_options,
        index=default_index,
        key=f"stage_type_input_{i}")

    st.session_state[f"stage_budget_{i}"] = st.sidebar.number_input(
        f"Stage {i+1} budget",
        min_value=0.0,
        value=float(st.session_state.get(f"stage_budget_{i}", 5_000_000.0)),
        step=5000000.0,
        format="%.0f",
        key=f"stage_budget_input_{i}")

    if st.session_state[f"stage_type_{i}"] == "Single Genre":
        default_genre = st.session_state.get(f"stage_genre_{i}", "Pop")
        genre_options = sorted(BROAD_GENRES)
        default_index = genre_options.index(default_genre) if default_genre in genre_options else 0

        st.session_state[f"stage_genre_{i}"] = st.sidebar.selectbox(
            f"Stage {i+1} genre",
            options=genre_options,
            index=default_index,
            key=f"stage_genre_input_{i}")

    elif st.session_state[f"stage_type_{i}"] == "Multi Genre":
        st.session_state[f"stage_genres_{i}"] = st.sidebar.multiselect(
            f"Stage {i+1} genres",
            options=sorted(BROAD_GENRES),
            default=st.session_state.get(f"stage_genres_{i}", ["Pop"]),
            key=f"stage_genres_input_{i}")

total_budget = sum(float(st.session_state.get(f"stage_budget_{i}", 0.0)) for i in range(n_stages))

run_model = st.sidebar.button("Run optimization")

# Run optimization
if run_model:
    st.session_state["festival_name"] = festival_name
    st.session_state["n_stages"] = n_stages
    st.session_state["n_days"] = n_days
    st.session_state["performances_per_day_per_stage"] = performances_per_day_per_stage
    st.session_state["total_budget"] = total_budget
    st.session_state["hit_percentile"] = hit_percentile

    try:
        model_output = run_festival_model(
            session_state=st.session_state,
            database_path=DATABASE_PATH,
            n_stages=n_stages,
            n_days=n_days,
            performances_per_day_per_stage=performances_per_day_per_stage,
            total_budget=float(total_budget),
            hit_percentile=float(hit_percentile),
            objective="max_appeal")
        st.session_state["result"] = model_output
        st.session_state["worst_result"] = None
        st.session_state["comparison_table"] = None
    except Exception as e:
        st.session_state["result"] = None
        st.error(f"Error: {e}")


result = st.session_state.get("result", None)
if result is None:
    st.stop()

# Show results
st.title(festival_name)

lineup = result["lineup"]
budget = result["budget"]
total_cost = result["total_cost"]
total_appeal = result["total_appeal"]
selected_artists = result["selected_artists"]
genre_distribution = result["genre_distribution"]
raw_result = result["raw_result"]

# KPIs
st.header("Main results")
k1, k2, k3 = st.columns(3)
k1.metric("Total cost", fmt_money(total_cost))
k2.metric("Total appeal", fmt_num(total_appeal, 1))
k3.metric("Selected artists", selected_artists)

# Budget table
st.header("Budget summary")
st.dataframe(prepare_budget_table(budget), use_container_width=True, hide_index=True)

# Lineup
st.header("Lineup")

stage_options = ["All stages"]
if "stage" in lineup.columns:
    stage_options += sorted(lineup["stage"].dropna().unique().tolist())

selected_stage = st.selectbox("Select stage", options=stage_options)
filtered_lineup = lineup_stage_filter(lineup, selected_stage)
st.dataframe(prepare_lineup_table(filtered_lineup), use_container_width=True, hide_index=True)

# Charts
st.header("Charts")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Budget vs cost by stage")
    fig_budget = make_budget_chart(budget)
    st.plotly_chart(fig_budget, use_container_width=True)

with col2:
    st.subheader("Appeal by stage")
    fig_appeal = make_appeal_chart(budget)
    st.plotly_chart(fig_appeal, use_container_width=True)

# Genre pie + artist table
st.header("Genre distribution")

col1, col2 = st.columns([1.1, 1.0])

with col1:
    fig_genre = make_genre_pie_chart(genre_distribution)
    st.plotly_chart(fig_genre, use_container_width=True)

with col2:
    genre_options = genre_distribution["Genre"].tolist()
    selected_genre = st.selectbox("Select genre", options=genre_options)
    genre_artist_table = get_artists_by_genre(lineup, selected_genre)

    genre_artist_table["Appeal"] = genre_artist_table["Appeal"].apply(lambda x: fmt_num(x, 1))
    genre_artist_table["Cost"] = genre_artist_table["Cost"].apply(fmt_money)
    st.dataframe(genre_artist_table, use_container_width=True, hide_index=True)

# Release decade analysis
release_df = build_lineup_release_data(lineup, DATABASE_PATH)
release_summary = build_release_summary(release_df)

# Album release analysis
st.header("Release profile of the selected lineup")

# KPIs
st.subheader("Key release year statistics")
k1, k2, k3, k4 = st.columns(4)
avg_year = int(round(release_summary["average_release_year"]))
oldest_year = release_summary["oldest_year"]
newest_year = release_summary["newest_year"]
median_year = int(round(release_summary["median_release_year"]))

k1.metric("Oldest release year", oldest_year)
k2.metric("Newest release year", newest_year)
k3.metric("Average release year", avg_year)
k4.metric("Median release year", median_year)

st.subheader("Release timeline by genre and decade")
st.write("The chart below shows how the selected artists' albums are distributed across decades and broad genres.")
decade_genre_album_counts = build_decade_genre_album_counts(release_df)

fig_genre_area = make_decade_genre_album_area_chart(decade_genre_album_counts)
st.plotly_chart(fig_genre_area, use_container_width=True)

st.subheader("Distribution of album release years")

oldest_albums = release_summary["oldest_albums"]
newest_albums = release_summary["newest_albums"]
col1, col2 = st.columns([1.0, 0.5])

with col1:
    fig_boxplot = make_release_year_boxplot(release_df)
    st.plotly_chart(fig_boxplot, use_container_width=True)

with col2:
    st.info(
        f"**Artist(s) with the oldest album(s):** {', '.join(oldest_albums) if oldest_albums else '-'}\n\n"
        f"**Artist(s) with the newest album(s):** {', '.join(newest_albums) if newest_albums else '-'}")

# Best vs worst solution
st.header("Best vs worst solution comparison")
compare_solutions = st.button("Create comparison with worst solution")

if compare_solutions:
    try:
        worst_result = run_festival_model(
            session_state=st.session_state,
            database_path=DATABASE_PATH,
            n_stages=n_stages,
            n_days=n_days,
            performances_per_day_per_stage=performances_per_day_per_stage,
            total_budget=float(total_budget),
            hit_percentile=float(hit_percentile),
            objective="min_appeal")

        comparison_table = build_solution_comparison(result, worst_result)
        comparison_table["Total Cost"] = comparison_table["Total Cost"].apply(fmt_money)
        comparison_table["Total Appeal"] = comparison_table["Total Appeal"].apply(lambda x: fmt_num(x, 1))

        st.session_state["worst_result"] = worst_result
        st.session_state["comparison_table"] = comparison_table

    except Exception as e:
        st.session_state["worst_result"] = None
        st.session_state["comparison_table"] = None
        st.error(f"Error: {e}")

#Comparison table
comparison_table = st.session_state.get("comparison_table", None)
worst_result = st.session_state.get("worst_result", None)

if comparison_table is not None and worst_result is not None:
    st.subheader("Appeal comparison across stages")

    fig_appeal_compare = make_appeal_comparison_chart(
        result["budget"],
        worst_result["budget"])
    if fig_appeal_compare is not None:
        st.plotly_chart(fig_appeal_compare, use_container_width=True)

    st.subheader("Solution summary comparison")
    st.dataframe(comparison_table, use_container_width=True, hide_index=True)
    col1, col2 = st.columns(2)
    with col1:
        render_solution_comparison_block(worst_result, "Worst solution (Min Appeal)", "worst")

    with col2:
        render_solution_comparison_block(result, "Best solution (Max Appeal)", "best")