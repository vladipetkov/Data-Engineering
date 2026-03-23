import streamlit as st
import base64
import time
from pathlib import Path

from lineup_files.stage import BROAD_GENRES
from lineup_files.festival_analytics_styled import (
    NEW_THEME,
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
    build_excel_file,
    get_artists_by_genre,
    build_lineup_release_data,
    build_decade_genre_album_counts,
    make_decade_genre_album_area_chart,
    make_release_year_boxplot,
    build_release_summary,
    build_solution_comparison,
    render_solution_comparison_block,
    make_appeal_comparison_chart,
)
logo_path = Path(__file__).parent.parent / "supporting" / "logo.png"
st.logo(logo_path, size = "large")
st.set_page_config(page_title="Festival Dashboard", layout="wide")

BASE_DIR = Path(__file__).resolve().parents[1]
LINEUP_DIR = BASE_DIR / "lineup_files"

DATABASE_PATH = LINEUP_DIR / "spotify_database.db"
INTRO_VIDEO_PATH = LINEUP_DIR / "festival_intro.mp4"
NAV_VIDEO_PATH = LINEUP_DIR / "reverse_festival.mp4"

MAIN_PAGE_PATH = "main.py"

def file_to_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()

def play_fullscreen_intro(video_path: Path, seconds: float = 4):
    if not video_path.exists():
        return

    video_b64 = file_to_base64(video_path)

    st.markdown(f"""
    <style>
    .intro-overlay {{
        position: fixed;
        inset: 0;
        z-index: 999999999;
        background: black;
        display: flex;
        align-items: center;
        justify-content: center;
    }}

    .intro-overlay video {{
        width: 100vw;
        height: 100vh;
        object-fit: cover;
    }}
    </style>

    <div class="intro-overlay">
        <video autoplay muted playsinline>
            <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
        </video>
    </div>
    """, unsafe_allow_html=True)

    time.sleep(seconds)
    st.empty()

if st.session_state.get("play_event_planning_intro", False):
    play_fullscreen_intro(INTRO_VIDEO_PATH, seconds=4)
    st.session_state["play_event_planning_intro"] = False
    st.rerun()


def file_to_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()


def img_to_data_uri(path: Path):
    if not path.exists():
        return None
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


hero_bg = img_to_data_uri(Path("/mnt/data/99b99f76-8bf5-49fc-a0d3-271e1f829fbf.png"))


def play_fullscreen_video(video_path: Path, seconds: float):
    if not video_path.exists():
        return
    video_b64 = file_to_base64(video_path)
    intro = st.empty()
    with intro.container():
        st.markdown(
            f"""
            <style>
            .intro-wrap {{
                position: fixed;
                inset: 0;
                background: black;
                z-index: 999999;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .intro-wrap video {{
                width: 100vw;
                height: 100vh;
                object-fit: cover;
            }}
            </style>
            <div class="intro-wrap">
                <video autoplay muted playsinline>
                    <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
                </video>
            </div>
            """,
            unsafe_allow_html=True,
        )
    time.sleep(seconds)
    intro.empty()

if st.session_state.get("event_planning_play_nav_intro", False):
    target = st.session_state.get("event_planning_target_page")
    video_b64 = base64.b64encode(Path(NAV_VIDEO_PATH).read_bytes()).decode()
    st.markdown(f"""
    <style>
    .overlay-video {{
        position: fixed;
        inset: 0;
        background: black;
        z-index: 999999999;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    .overlay-video video {{
        width: 100vw;
        height: 100vh;
        object-fit: cover;
    }}
    </style>
    <div class="overlay-video">
        <video autoplay muted playsinline>
            <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
        </video>
    </div>
    """, unsafe_allow_html=True)
    time.sleep(5.5)
    st.session_state["event_planning_play_nav_intro"] = False
    st.session_state["event_planning_target_page"] = None

    if target:
        st.switch_page(target)

    st.stop()

def apply_new_dashboard_style():
    hero_style = (
        f"background-image: linear-gradient(rgba(255,47,95,0.82), rgba(255,47,95,0.82)), url('{hero_bg}');"
        if hero_bg
        else "background: linear-gradient(135deg, #ff2f5f 0%, #ef336a 100%);"
    )

    st.markdown(
        f'''
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@400;600;700;800&display=swap');

        :root {{
            --sz-pink: {NEW_THEME["pink"]};
            --sz-yellow: {NEW_THEME["yellow"]};
            --sz-blue: {NEW_THEME["blue"]};
            --sz-lav: {NEW_THEME["lavender"]};
            --sz-card: {NEW_THEME["card"]};
            --sz-white: {NEW_THEME["ink"]};
        }}

        html, body, [class*="css"] {{
            font-family: 'Baloo 2', cursive;
        }}

        .stApp {{
            background:
                radial-gradient(circle at 15% 20%, rgba(247,229,59,0.22) 0, rgba(247,229,59,0.22) 5px, transparent 6px),
                radial-gradient(circle at 85% 30%, rgba(255,255,255,0.16) 0, rgba(255,255,255,0.16) 7px, transparent 8px),
                radial-gradient(circle at 75% 75%, rgba(201,140,194,0.28) 0, rgba(201,140,194,0.28) 90px, transparent 91px),
                linear-gradient(135deg, #ff2f5f 0%, #ef336a 100%);
            color: white;
        }}

        .block-container {{
            padding-top: 1.25rem;
            padding-bottom: 3rem;
        }}

        h1, h2, h3, h4, .stMarkdown, label, p, span {{
            color: white !important;
        }}

        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #c98cc2 0%, #b976b1 100%);
            border-right: 4px solid var(--sz-yellow);
        }}

        [data-testid="stSidebar"] * {{
            color: white !important;
        }}

        .hero-banner {{
            {hero_style}
            background-size: cover;
            background-position: center;
            border: 4px solid var(--sz-yellow);
            border-radius: 32px;
            padding: 1.2rem 1.6rem;
            box-shadow: 0 14px 0 rgba(31,88,199,0.95);
            margin-bottom: 1.1rem;
        }}

        .hero-title {{
            font-size: 3rem;
            line-height: 1;
            font-weight: 800;
            letter-spacing: 0.03em;
            text-transform: uppercase;
            color: white !important;
            text-shadow: 4px 4px 0 rgba(31,88,199,0.95);
            margin-bottom: 0.25rem;
        }}

        .feature-card {{
            background: rgba(201,140,194,0.9);
            border: 3px solid white;
            border-radius: 28px;
            padding: 1rem;
            box-shadow: 7px 7px 0 rgba(31,88,199,0.95);
            min-height: 280px;
            display: flex;
            flex-direction: column;
        }}

        .feature-card.alt {{
            background: rgba(31,88,199,0.92);
        }}

        .feature-card h3 {{
            text-transform: uppercase;
            letter-spacing: 0.03em;
            font-weight: 800;
            margin-bottom: 0.7rem;
        }}

        .feature-card .feature-caption {{
            color: white !important;
            font-size: 0.95rem;
            line-height: 1.5;
            margin-top: auto;
        }}

        .section-kicker {{
            display: inline-block;
            padding: 0.2rem 0.8rem;
            border-radius: 999px;
            background: var(--sz-yellow);
            color: var(--sz-blue) !important;
            font-weight: 800;
            text-transform: uppercase;
            margin-bottom: 0.35rem;
        }}

        div[data-testid="stMetric"] {{
            background: rgba(31,88,199,0.92);
            border: 3px solid white;
            border-radius: 26px;
            padding: 0.6rem 0.8rem;
            box-shadow: 7px 7px 0 rgba(247,229,59,0.95);
        }}

        div[data-testid="stMetricLabel"] > div,
        div[data-testid="stMetricValue"] > div {{
            color: white !important;
            font-weight: 800;
        }}

        .stButton > button,
        .stDownloadButton > button,
        div[data-baseweb="select"] > div,
        .stTextInput input,
        .stNumberInput input,
        .stMultiSelect [data-baseweb="tag"],
        .stTextArea textarea {{
            border-radius: 22px !important;
        }}

        .stButton > button {{
            background: var(--sz-yellow);
            color: var(--sz-blue) !important;
            border: 3px solid white;
            font-weight: 800;
            text-transform: uppercase;
            box-shadow: 5px 5px 0 rgba(31,88,199,0.95);
        }}

        .stButton > button:hover {{
            border-color: white;
            color: var(--sz-pink) !important;
            transform: translateY(-1px);
        }}

        .stDataFrame, div[data-testid="stTable"] {{
            background: rgba(201,140,194,0.18);
            border-radius: 24px;
            padding: 0.35rem;
            border: 3px solid white;
        }}

        div[data-testid="stInfo"] {{
            background: rgba(31,88,199,0.88);
            border: 3px solid white;
            border-radius: 24px;
            color: white !important;
        }}

        hr {{
            border-color: rgba(255,255,255,0.25);
        }}

        [data-testid="stHeader"] {{
            background: linear-gradient(135deg, #ff2f5f 0%, #ef336a 100%) !important;
            border-bottom: 4px solid var(--sz-yellow);
        }}

        [data-testid="stToolbar"] {{
            background: transparent !important;
        }}

        [data-testid="stDecoration"] {{
            display: none;
        }}
        </style>
        ''',
        unsafe_allow_html=True,
    )


apply_new_dashboard_style()

st.markdown(
    '''
    <div class="hero-banner">
        <div class="hero-title">Festival Optimization Dashboard</div>
    </div>
    ''',
    unsafe_allow_html=True,
)

feature_titles = [
    ("Appeal score", "Based on popularity, followers, and number of hits (newer the hit is the more it counts, giving it a momentum)."),
    ("Cost estimation", "Estimated booking cost based on popularity and fan base."),
    ("Genre classification", "Artists grouped into broad genres using keywords."),
    ("Stage requirements", "Assigns artists to stages based on genre and budget."),
    ("Optimization", "Maximizes total appeal under budget and stage constraints."),
]

cols = st.columns(5)
for idx, col in enumerate(cols):
    with col:
        card_class = "feature-card alt" if idx % 2 else "feature-card"
        st.markdown(
            f'''
            <div class="{card_class}">
                <h3>{feature_titles[idx][0]}</h3>
                <div class="feature-caption">{feature_titles[idx][1]}</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

st.session_state.setdefault("festival_name", "My Festival")
st.session_state.setdefault("n_stages", 3)
st.session_state.setdefault("n_days", 4)
st.session_state.setdefault("performances_per_day_per_stage", 4)
st.session_state.setdefault("hit_percentile", 0.97)

ensure_stage_defaults(st.session_state, int(st.session_state["n_stages"]))

st.sidebar.markdown("## Navigation")
if st.sidebar.button("Main Page"):
    st.session_state["event_planning_target_page"] = MAIN_PAGE_PATH
    st.session_state["event_planning_play_nav_intro"] = True
    st.rerun()

st.sidebar.header("Inputs")

festival_name = st.sidebar.text_input("Festival name", value=st.session_state["festival_name"])
n_stages = st.sidebar.number_input("Number of stages", min_value=1, max_value=8, value=st.session_state["n_stages"], step=1)
n_days = st.sidebar.number_input("Number of festival days", min_value=1, max_value=14, value=st.session_state["n_days"], step=1)
performances_per_day_per_stage = st.sidebar.number_input(
    "Performances per day per stage",
    min_value=1,
    max_value=12,
    value=st.session_state["performances_per_day_per_stage"],
    step=1,
)
hit_percentile = st.sidebar.slider(
    "Hit song threshold",
    min_value=0.00,
    max_value=0.99,
    value=float(st.session_state["hit_percentile"]),
    step=0.01,
)
st.sidebar.caption("Defines how popular a song must be to count as a hit. Higher values mean only top songs contribute to artist appeal.")

n_stages = int(n_stages)
n_days = int(n_days)
performances_per_day_per_stage = int(performances_per_day_per_stage)

ensure_stage_defaults(st.session_state, n_stages)

st.sidebar.subheader("Stage setup")

for i in range(n_stages):
    st.sidebar.markdown(f"### Stage {i+1}")

    st.session_state[f"stage_name_{i}"] = st.sidebar.text_input(
        f"Stage {i+1} name",
        value=st.session_state.get(f"stage_name_{i}", f"Stage {i+1}"),
        key=f"stage_name_input_{i}",
    )

    default_type = st.session_state.get(f"stage_type_{i}", "Main" if i == 0 else "Single Genre")
    type_options = ["Main", "Single Genre", "Multi Genre"]
    default_index = type_options.index(default_type) if default_type in type_options else 1

    st.session_state[f"stage_type_{i}"] = st.sidebar.selectbox(
        f"Stage {i+1} type",
        options=type_options,
        index=default_index,
        key=f"stage_type_input_{i}",
    )

    st.session_state[f"stage_budget_{i}"] = st.sidebar.number_input(
        f"Stage {i+1} budget",
        min_value=0.0,
        value=float(st.session_state.get(f"stage_budget_{i}", 5_000_000.0)),
        step=5000000.0,
        format="%.0f",
        key=f"stage_budget_input_{i}",
    )

    if st.session_state[f"stage_type_{i}"] == "Single Genre":
        default_genre = st.session_state.get(f"stage_genre_{i}", "Pop")
        genre_options = sorted(BROAD_GENRES)
        default_index = genre_options.index(default_genre) if default_genre in genre_options else 0

        st.session_state[f"stage_genre_{i}"] = st.sidebar.selectbox(
            f"Stage {i+1} genre",
            options=genre_options,
            index=default_index,
            key=f"stage_genre_input_{i}",
        )

    elif st.session_state[f"stage_type_{i}"] == "Multi Genre":
        st.session_state[f"stage_genres_{i}"] = st.sidebar.multiselect(
            f"Stage {i+1} genres",
            options=sorted(BROAD_GENRES),
            default=st.session_state.get(f"stage_genres_{i}", ["Pop"]),
            key=f"stage_genres_input_{i}",
        )

total_budget = sum(float(st.session_state.get(f"stage_budget_{i}", 0.0)) for i in range(n_stages))

run_model = st.sidebar.button("Run optimization")

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
            database_path=str(DATABASE_PATH),
            n_stages=n_stages,
            n_days=n_days,
            performances_per_day_per_stage=performances_per_day_per_stage,
            total_budget=float(total_budget),
            hit_percentile=float(hit_percentile),
            objective="max_appeal",
        )
        st.session_state["result"] = model_output
        st.session_state["worst_result"] = None
        st.session_state["comparison_table"] = None
    except Exception as e:
        st.session_state["result"] = None
        st.error(f"Error: {e}")

result = st.session_state.get("result", None)
if result is None:
    st.info("Run the optimization to generate your lineup and see the results here!")
    st.stop()

st.markdown('<div class="section-kicker">Festival results</div>', unsafe_allow_html=True)
st.title(festival_name)

lineup = result["lineup"]
budget = result["budget"]
solver_status = result["solver_status"]
total_cost = result["total_cost"]
total_appeal = result["total_appeal"]
selected_artists = result["selected_artists"]
genre_distribution = result["genre_distribution"]

st.header("Main results")
k1, k2, k3 = st.columns(3)
k1.metric("Total cost", fmt_money(total_cost))
k2.metric("Total appeal", fmt_num(total_appeal, 1))
k3.metric("Selected artists", selected_artists)

st.header("Budget summary")
st.dataframe(prepare_budget_table(budget), use_container_width=True, hide_index=True)

st.header("Lineup")
excel_data = build_excel_file(result, festival_name)

st.download_button(
    label="Download result as Excel",
    data=excel_data,
    file_name=f"{festival_name.lower().replace(' ', '_')}_result.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

stage_options = ["All stages"]
if "stage" in lineup.columns:
    stage_options += sorted(lineup["stage"].dropna().unique().tolist())

selected_stage = st.selectbox("Select stage", options=stage_options)
filtered_lineup = lineup_stage_filter(lineup, selected_stage)
st.dataframe(prepare_lineup_table(filtered_lineup), use_container_width=True, hide_index=True)

st.header("Charts")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Budget vs cost by stage")
    st.plotly_chart(make_budget_chart(budget), use_container_width=True)

with col2:
    st.subheader("Appeal by stage")
    st.plotly_chart(make_appeal_chart(budget), use_container_width=True)

st.header("Genre distribution")
col1, col2 = st.columns([1.1, 1.0])

with col1:
    st.plotly_chart(make_genre_pie_chart(genre_distribution), use_container_width=True)

with col2:
    genre_options = genre_distribution["Genre"].tolist()
    selected_genre = st.selectbox("Select genre", options=genre_options)
    genre_artist_table = get_artists_by_genre(lineup, selected_genre)
    genre_artist_table["Appeal"] = genre_artist_table["Appeal"].apply(lambda x: fmt_num(x, 1))
    genre_artist_table["Cost"] = genre_artist_table["Cost"].apply(fmt_money)
    st.dataframe(genre_artist_table, use_container_width=True, hide_index=True)

release_df = build_lineup_release_data(lineup, str(DATABASE_PATH))
release_summary = build_release_summary(release_df)

st.header("Release profile of the selected lineup")

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
st.plotly_chart(make_decade_genre_album_area_chart(decade_genre_album_counts), use_container_width=True)

st.subheader("Distribution of album release years")

oldest_albums = release_summary["oldest_albums"]
newest_albums = release_summary["newest_albums"]
col1, col2 = st.columns([1.0, 0.5])

with col1:
    st.plotly_chart(make_release_year_boxplot(release_df), use_container_width=True)

with col2:
    st.info(
        f"**Artist(s) with the oldest album(s):** {', '.join(oldest_albums) if oldest_albums else '-'}\n\n"
        f"**Artist(s) with the newest album(s):** {', '.join(newest_albums) if newest_albums else '-'}"
    )

st.header("Best vs worst solution comparison")
compare_solutions = st.button("Create comparison with worst solution")

if compare_solutions:
    try:
        worst_result = run_festival_model(
            session_state=st.session_state,
            database_path=str(DATABASE_PATH),
            n_stages=n_stages,
            n_days=n_days,
            performances_per_day_per_stage=performances_per_day_per_stage,
            total_budget=float(total_budget),
            hit_percentile=float(hit_percentile),
            objective="min_appeal",
        )

        comparison_table = build_solution_comparison(result, worst_result)
        comparison_table["Total Cost"] = comparison_table["Total Cost"].apply(fmt_money)
        comparison_table["Total Appeal"] = comparison_table["Total Appeal"].apply(lambda x: fmt_num(x, 1))

        st.session_state["worst_result"] = worst_result
        st.session_state["comparison_table"] = comparison_table

    except Exception as e:
        st.session_state["worst_result"] = None
        st.session_state["comparison_table"] = None
        st.error(f"Error: {e}")

comparison_table = st.session_state.get("comparison_table", None)
worst_result = st.session_state.get("worst_result", None)

if comparison_table is not None and worst_result is not None:
    st.subheader("Appeal comparison across stages")
    fig_appeal_compare = make_appeal_comparison_chart(result["budget"], worst_result["budget"])
    if fig_appeal_compare is not None:
        st.plotly_chart(fig_appeal_compare, use_container_width=True)

    st.subheader("Solution summary comparison")
    st.dataframe(comparison_table, use_container_width=True, hide_index=True)
    col1, col2 = st.columns(2)
    with col1:
        render_solution_comparison_block(worst_result, "Worst solution (Min Appeal)", "worst")
    with col2:
        render_solution_comparison_block(result, "Best solution (Max Appeal)", "best")
