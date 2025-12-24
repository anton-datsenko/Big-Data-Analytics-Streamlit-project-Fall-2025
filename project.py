import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# PAGE CONFIG
st.set_page_config(
    page_title="Minecraft World Analytics",
    layout="wide"
)

st.title("Minecraft World Analytics")

# COLOR THEME
COLOR_SEQ = px.colors.qualitative.Bold
CONTINUOUS_SCALE = px.colors.sequential.Viridis

# DATA GENERATION
@st.cache_data
def generate_data(n_players=120, max_days=365):
    np.random.seed(42)

    players = [f"Player_{i}" for i in range(1, n_players + 1)]
    styles = ["Builder", "Miner", "Fighter", "Explorer"]
    biomes = ["Forest", "Plains", "Desert", "Mountains", "Swamp", "Nether", "End"]
    resources = ["Diamond", "Iron", "Gold", "Redstone", "Coal"]
    death_causes = ["Lava", "Creeper", "Fall", "PvP", "Skeleton", "Void"]
    modes = ["Survival", "Creative", "Hardcore"]

    activity = pd.DataFrame({
        "day": np.random.randint(1, max_days + 1, n_players * max_days),
        "player": np.random.choice(players, n_players * max_days),
        "hours_played": np.random.gamma(2.2, 1.8, n_players * max_days),
        "style": np.random.choice(styles, n_players * max_days),
        "mode": np.random.choice(modes, n_players * max_days, p=[0.55, 0.25, 0.20])
    })

    mining = pd.DataFrame({
        "day": np.random.randint(1, max_days + 1, 12000),
        "player": np.random.choice(players, 12000),
        "resource": np.random.choice(resources, 12000, p=[0.08, 0.32, 0.18, 0.22, 0.20]),
        "y_level": np.random.randint(-64, 128, 12000),
        "biome": np.random.choice(biomes, 12000),
        "mode": np.random.choice(modes, 12000, p=[0.55, 0.25, 0.20])
    })

    economy = pd.DataFrame({
        "day": np.random.randint(1, max_days + 1, n_players * 8),
        "player": np.random.choice(players, n_players * 8),
        "balance": np.random.lognormal(3.2, 0.9, n_players * 8),
        "mode": np.random.choice(modes, n_players * 8),
        "cheater": np.random.choice([True, False], n_players * 8, p=[0.12, 0.88])
    })

    deaths = pd.DataFrame({
        "day": np.random.randint(1, max_days + 1, 4000),
        "player": np.random.choice(players, 4000),
        "cause": np.random.choice(death_causes, 4000),
        "mode": np.random.choice(modes, 4000)
    })

    return activity, mining, economy, deaths


activity, mining, economy, deaths = generate_data()

# SIDEBAR
st.sidebar.header("Settings")

mode = st.sidebar.selectbox(
    "Mode",
    ["Survival", "Creative", "Hardcore"]
)

day_range = st.sidebar.slider(
    "Range of days",
    1, 365, (1, 365)
)

selected_biomes = st.sidebar.multiselect(
    "Biomes",
    options=sorted(mining["biome"].unique()),
    default=sorted(mining["biome"].unique())
)

selected_resources = st.sidebar.multiselect(
    "Resources",
    options=sorted(mining["resource"].unique()),
    default=sorted(mining["resource"].unique())
)

active_only = st.sidebar.checkbox("Only active players (>2 hours)")
honest_only = st.sidebar.checkbox("No cheaters")


# GLOBAL FILTERING
activity_f = activity[
    (activity["day"].between(*day_range)) &
    (activity["mode"] == mode)
]

if active_only:
    activity_f = activity_f[activity_f["hours_played"] > 2]

mining_f = mining[
    (mining["day"].between(*day_range)) &
    (mining["mode"] == mode) &
    (mining["biome"].isin(selected_biomes)) &
    (mining["resource"].isin(selected_resources))
]

economy_f = economy[
    (economy["day"].between(*day_range)) &
    (economy["mode"] == mode)
]

if honest_only:
    economy_f = economy_f[~economy_f["cheater"]]

deaths_f = deaths[
    (deaths["day"].between(*day_range)) &
    (deaths["mode"] == mode)
]

# TABS
tab_stats, tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Statistics",
    "Player Analytics",
    "Resource Mining",
    "Biomes",
    "Economy",
    "Chaos",
    "Raw Data",
    "Code Overview"
])

# TAB — STATISTICS
with tab_stats:
    st.subheader("Key Metrics Overview")

    # METRICS CALCULATION
    unique_players = activity_f["player"].nunique()

    total_playtime = activity_f["hours_played"].sum()
    avg_playtime = (
        total_playtime / unique_players
        if unique_players > 0 else 0
    )

    mining_events = len(mining_f)
    deaths_count = len(deaths_f)

    chaos_index = (
        deaths_count / unique_players
        if unique_players > 0 else 0
    )

    top_biome = (
        mining_f["biome"].value_counts().idxmax()
        if not mining_f.empty else "—"
    )

    top_resource = (
        mining_f["resource"].value_counts().idxmax()
        if not mining_f.empty else "—"
    )

    #  KPI ROW 1
    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Active Players",
        f"{unique_players}"
    )

    col2.metric(
        "Avg Playtime / Player",
        f"{avg_playtime:.2f} h"
    )

    col3.metric(
        "Total Playtime",
        f"{total_playtime:.0f} h"
    )

    col4.metric(
        "Mining Events",
        f"{mining_events}"
    )

    # KPI ROW 2 
    col5, col6, col7, col8 = st.columns(4)

    col5.metric(
        "Deaths Recorded",
        f"{deaths_count}"
    )

    col6.metric(
        "Chaos Index",
        f"{chaos_index:.2f}"
    )

    col7.metric(
        "Top Biome",
        top_biome
    )

    col8.metric(
        "Top Resource",
        top_resource
    )

# TAB 1 — PLAYERS
with tab1:
    daily = activity_f.groupby("day")["hours_played"].sum().reset_index()

    fig = px.line(
        daily,
        x="day",
        y="hours_played",
        color_discrete_sequence=COLOR_SEQ,
        title="Player Activity Over Time"
    )
    st.plotly_chart(fig, use_container_width=True)

    top_players = (
        activity_f.groupby("player")["hours_played"]
        .sum()
        .sort_values(ascending=False)
        .head(15)
        .reset_index()
    )

    fig2 = px.bar(
        top_players,
        x="player",
        y="hours_played",
        color="hours_played",
        color_continuous_scale=CONTINUOUS_SCALE,
        title="Top Players"
    )
    st.plotly_chart(fig2, use_container_width=True)

# TAB 2 — MINING
with tab2:
    fig = px.histogram(
        mining_f,
        x="y_level",
        color="resource",
        nbins=60,
        color_discrete_sequence=COLOR_SEQ,
        title="Mining Depth Distribution"
    )
    st.plotly_chart(fig, use_container_width=True)

    biome_res = mining_f.groupby(["biome", "resource"]).size().reset_index(name="count")

    fig2 = px.bar(
        biome_res,
        x="biome",
        y="count",
        color="resource",
        color_discrete_sequence=COLOR_SEQ,
        barmode="group",
        title="Resources by Biome"
    )
    st.plotly_chart(fig2, use_container_width=True)

# TAB 3 — BIOMES
with tab3:
    biome_size = mining_f["biome"].value_counts().reset_index()
    biome_size.columns = ["biome", "area"]

    fig = px.treemap(
        biome_size,
        path=["biome"],
        values="area",
        color="area",
        color_continuous_scale=CONTINUOUS_SCALE,
        title="Biome Distribution"
    )
    st.plotly_chart(fig, use_container_width=True)

# TAB 4 — ECONOMY
with tab4:
    wealth = economy_f.groupby("player")["balance"].sum().reset_index()

    fig = px.histogram(
        wealth,
        x="balance",
        nbins=40,
        color_discrete_sequence=COLOR_SEQ,
        title="Wealth Distribution"
    )
    st.plotly_chart(fig, use_container_width=True)

    richest = wealth.sort_values("balance", ascending=False).head(15)

    fig2 = px.bar(
        richest,
        x="player",
        y="balance",
        color="balance",
        color_continuous_scale=CONTINUOUS_SCALE,
        title="Richest Players"
    )
    st.plotly_chart(fig2, use_container_width=True)


# TAB 5 — CHAOS
with tab5:
    causes = deaths_f["cause"].value_counts().reset_index()
    causes.columns = ["cause", "count"]

    fig = px.bar(
        causes,
        x="cause",
        y="count",
        color="count",
        color_continuous_scale=CONTINUOUS_SCALE,
        title="Death Causes"
    )
    st.plotly_chart(fig, use_container_width=True)

    chaos_index = len(deaths_f) / max(activity_f["player"].nunique(), 1)

    st.metric(
        "Chaos Index",
        f"{chaos_index:.2f}"
    )

activity_df = activity.copy()
activity_df["source"] = "Activity"

mining_df = mining.copy()
mining_df["source"] = "Mining"

economy_df = economy.copy()
economy_df["source"] = "Economy"

deaths_df = deaths.copy()
deaths_df["source"] = "Deaths"

all_data = pd.concat([activity_df, mining_df, economy_df, deaths_df], ignore_index=True)

# TAB 6 — RAW DATA
import streamlit as st
from st_aggrid import AgGrid

with tab6:
    st.subheader("Activity Data")
    AgGrid(activity)

    st.subheader("Mining Data")
    AgGrid(mining)

    st.subheader("Economy Data")
    AgGrid(economy)

    st.subheader("Deaths Data")
    AgGrid(deaths)

# TAB 7 — CODE OVERVIEW
with tab7:
    # DATA GENERATION
    with st.container():
        st.markdown("## Data Generation")

        col1, col2 = st.columns([2, 3])

        with col1:
            st.markdown("""
            Synthetic data is generated once and cached.
            It simulates player activity, mining events,
            economy transactions and deaths.
            """)

        with col2:
            st.code("""
@st.cache_data
def generate_data(n_players=120, max_days=365):
    players = [...]
    activity = pd.DataFrame(...)
    mining = pd.DataFrame(...)
    economy = pd.DataFrame(...)
    deaths = pd.DataFrame(...)
    return activity, mining, economy, deaths
""", language="python")

    # FILTERING
    with st.container():
        st.markdown("## Global Filtering Logic")

        col1, col2 = st.columns([3, 2])

        with col1:
            st.code("""
activity_f = activity[
    (activity["day"].between(*day_range)) &
    (activity["mode"] == mode)
]

mining_f = mining[
    (mining["day"].between(*day_range)) &
    (mining["mode"] == mode) &
    (mining["biome"].isin(selected_biomes)) &
    (mining["resource"].isin(selected_resources))
]
""", language="python")

        with col2:
            st.info("""
All visualizations depend on the same
filtered datasets, ensuring consistency
across tabs.
""")

    # VISUALIZATION
    with st.container():
        st.markdown("## Visualization Layer")

        with st.expander("Player Activity Visualization"):
            st.code("""
daily = activity_f.groupby("day")["hours_played"].sum().reset_index()

fig = px.line(
    daily,
    x="day",
    y="hours_played",
    title="Player Activity Over Time"
)
st.plotly_chart(fig)
""", language="python")

        with st.expander("Mining Analytics Visualization"):
            st.code("""
fig = px.histogram(
    mining_f,
    x="y_level",
    color="resource",
    nbins=60
)
st.plotly_chart(fig)
""", language="python")

    # CHAOS INDEX
    with st.container():
        st.markdown("## Chaos Index")

        col1, col2 = st.columns([3, 2])

        with col1:
            st.code("""
chaos_index = len(deaths_f) / max(
    activity_f["player"].nunique(), 1
)
""", language="python")

        with col2:
            st.caption("""
Normalized indicator measuring deaths
per active player within selected filters.
""")

# STATISTICS OVERVIEW
    with st.container():
        st.markdown("## Statistics Overview")

        col1, col2 = st.columns([3, 2])

        with col1:
            st.code("""
# Unique active players in selected period
unique_players = activity_f["player"].nunique()

# Total playtime (hours)
total_hours = activity_f["hours_played"].sum()

# Average playtime per player
avg_hours_per_player = (
    total_hours / unique_players
    if unique_players > 0 else 0
)

# Average session length
avg_session = activity_f["hours_played"].mean()

# Death rate per player
death_rate = (
    len(deaths_f) / unique_players
    if unique_players > 0 else 0
)
""", language="python")

        with col2:
            st.info("""
These metrics are recalculated dynamically
based on the selected day range, game mode,
biomes and resources.

They power the **Statistics** tab and KPI cards
shown across the dashboard.
""")

    # STREAMLIT FEATURES
    st.markdown("## Streamlit Features Demonstrated")

    st.markdown("""
    - Sidebar controls (selectbox, slider, multiselect, checkbox)
    - Cached data generation
    - Global reactive filtering
    - Tabs for logical separation
    - Containers and columns for layout
    - Expanders for progressive disclosure
    - Interactive Plotly charts
    - KPI metrics
    """)