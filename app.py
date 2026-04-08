from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="Extreme Poverty Dashboard",
    page_icon="📉",
    layout="wide",
)

DATA_DIR = Path(__file__).parent / "data"
SHARE_FILE = DATA_DIR / "share-of-population-in-extreme-poverty.csv"
PROJECTION_FILE = DATA_DIR / "projections-extreme-poverty-wb.csv"

DEFAULT_COUNTRIES = [
    "DR Congo",
    "Mozambique",
    "Malawi",
    "Burundi",
    "Central African Republic",
    "Madagascar",
]

REGION_ORDER = [
    "South Asia (WB)",
    "East Asia and Pacific (WB)",
    "Sub-Saharan Africa (WB)",
    "MENA, Afghanistan and Pakistan (WB)",
    "Latin America and Caribbean (WB)",
    "Europe and Central Asia (WB)",
    "North America (WB)",
]

OWID_COLORS = {
    "DR Congo": "#8c2d3e",
    "Mozambique": "#2f9e73",
    "Malawi": "#7a4bc2",
    "Burundi": "#4878b6",
    "Central African Republic": "#d95f02",
    "Madagascar": "#a97142",
    "South Asia (WB)": "#a97142",
    "East Asia and Pacific (WB)": "#e58b7a",
    "Sub-Saharan Africa (WB)": "#5b8cc9",
    "MENA, Afghanistan and Pakistan (WB)": "#557a2b",
    "Latin America and Caribbean (WB)": "#8b61c2",
    "Europe and Central Asia (WB)": "#4ab2b2",
    "North America (WB)": "#c84b4b",
}


@st.cache_data
def load_share_data() -> pd.DataFrame:
    df = pd.read_csv(SHARE_FILE)
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["Share of population in poverty ($3 a day)"] = pd.to_numeric(
        df["Share of population in poverty ($3 a day)"], errors="coerce"
    )
    df["Population"] = pd.to_numeric(df["Population"], errors="coerce")
    df = df.dropna(subset=["Entity", "Year"])
    df = df[df["Year"] >= 1990].copy()
    return df


@st.cache_data
def load_projection_data() -> pd.DataFrame:
    df = pd.read_csv(PROJECTION_FILE)
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["Number of people in poverty ($3 a day)"] = pd.to_numeric(
        df["Number of people in poverty ($3 a day)"], errors="coerce"
    )
    df = df.dropna(subset=["Entity", "Year", "Number of people in poverty ($3 a day)"])
    return df


share_df = load_share_data()
projection_df = load_projection_data()

country_df = share_df[
    share_df["Code"].notna()
    & (share_df["Code"].str.len() == 3)
    & share_df["Share of population in poverty ($3 a day)"].notna()
].copy()

all_years = sorted(country_df["Year"].astype(int).unique().tolist())
min_year, max_year = min(all_years), max(all_years)

if "selected_year" not in st.session_state:
    st.session_state.selected_year = 2022 if 2022 in all_years else max_year
if "playing" not in st.session_state:
    st.session_state.playing = False

if st.session_state.playing:
    st_autorefresh(interval=1200, key="poverty_player")
    current_idx = all_years.index(int(st.session_state.selected_year))
    if current_idx < len(all_years) - 1:
        st.session_state.selected_year = all_years[current_idx + 1]
    else:
        st.session_state.playing = False

st.title("Extreme Poverty Dashboard")
st.caption(
    "Data source: World Bank Poverty and Inequality Platform / Our World in Data. "
    "This app includes a year playback control so you can watch how country-level poverty patterns change over time."
)

with st.sidebar:
    st.header("Controls")

    year_value = st.slider(
        "Year",
        min_value=min_year,
        max_value=max_year,
        value=int(st.session_state.selected_year),
        step=1,
    )
    st.session_state.selected_year = year_value

    control_cols = st.columns(3)
    if control_cols[0].button("▶ Play", use_container_width=True):
        st.session_state.playing = True
        st.rerun()
    if control_cols[1].button("⏸ Pause", use_container_width=True):
        st.session_state.playing = False
        st.rerun()
    if control_cols[2].button("↺ Reset", use_container_width=True):
        st.session_state.playing = False
        st.session_state.selected_year = min_year
        st.rerun()

    available_countries = sorted(country_df["Entity"].unique().tolist())
    default_selected = [c for c in DEFAULT_COUNTRIES if c in available_countries]
    selected_countries = st.multiselect(
        "Countries for line chart",
        options=available_countries,
        default=default_selected,
    )

    region_options = sorted(country_df["World region according to OWID"].dropna().unique().tolist())
    selected_regions = st.multiselect(
        "Regions for bubble chart",
        options=region_options,
        default=region_options,
    )

    top_n = st.slider("Top countries table", min_value=5, max_value=20, value=10, step=1)

selected_year = int(st.session_state.selected_year)
selected_year_df = country_df[
    (country_df["Year"] == selected_year)
    & (country_df["World region according to OWID"].isin(selected_regions))
].copy()

metric_cols = st.columns(4)
metric_cols[0].metric("Selected year", f"{selected_year}")
metric_cols[1].metric(
    "Countries with data",
    f"{selected_year_df['Entity'].nunique():,}",
)
if not selected_year_df.empty:
    weighted_share = (
        (selected_year_df["Share of population in poverty ($3 a day)"] * selected_year_df["Population"]).sum()
        / selected_year_df["Population"].sum()
    )
    metric_cols[2].metric("Population-weighted poverty share", f"{weighted_share:.1f}%")
    max_row = selected_year_df.nlargest(1, "Share of population in poverty ($3 a day)").iloc[0]
    metric_cols[3].metric("Highest country in selected year", max_row["Entity"])
else:
    metric_cols[2].metric("Population-weighted poverty share", "N/A")
    metric_cols[3].metric("Highest country in selected year", "N/A")

line_tab, area_tab, bubble_tab = st.tabs([
    "Country trends",
    "Regional totals",
    "Year playback",
])

with line_tab:
    st.subheader("Share of population living in extreme poverty")
    st.write("Selected countries are shown as line charts. The dashed line marks the currently selected year.")

    if not selected_countries:
        st.info("Select at least one country from the sidebar.")
    else:
        line_df = country_df[country_df["Entity"].isin(selected_countries)].copy()

        fig_line = px.line(
            line_df,
            x="Year",
            y="Share of population in poverty ($3 a day)",
            color="Entity",
            markers=True,
            color_discrete_map=OWID_COLORS,
        )
        fig_line.add_vline(x=selected_year, line_dash="dash", line_color="gray")
        fig_line.update_traces(
            hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>Poverty share: %{y:.1f}%<extra></extra>"
        )
        fig_line.update_layout(
            template="plotly_white",
            height=620,
            legend_title_text="",
            margin=dict(l=40, r=40, t=30, b=20),
            yaxis_title="Share of population in poverty (%)",
            xaxis_title="",
        )
        fig_line.update_yaxes(range=[0, 100], ticksuffix="%")
        st.plotly_chart(fig_line, use_container_width=True)

with area_tab:
    st.subheader("Total population living in extreme poverty by world region")
    st.write("The dotted vertical line marks the start of the projection segment in the source chart.")

    area_df = projection_df[projection_df["Entity"].isin(REGION_ORDER)].copy()
    area_df["Entity"] = pd.Categorical(area_df["Entity"], categories=REGION_ORDER, ordered=True)
    area_df = area_df.sort_values(["Year", "Entity"])

    fig_area = px.area(
        area_df,
        x="Year",
        y="Number of people in poverty ($3 a day)",
        color="Entity",
        category_orders={"Entity": REGION_ORDER},
        color_discrete_map=OWID_COLORS,
    )
    fig_area.add_vline(x=2023, line_dash="dot", line_color="gray")
    fig_area.add_annotation(
        x=2023,
        y=area_df["Number of people in poverty ($3 a day)"].max() * 1.02,
        text="Projections by the World Bank",
        showarrow=False,
        font=dict(color="gray", size=12),
    )
    fig_area.add_vline(x=selected_year, line_dash="dash", line_color="black", opacity=0.5)
    fig_area.update_traces(
        hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>People in poverty: %{y:,.0f}<extra></extra>"
    )
    fig_area.update_layout(
        template="plotly_white",
        height=620,
        legend_title_text="",
        margin=dict(l=40, r=40, t=30, b=20),
        yaxis_title="People in poverty",
        xaxis_title="",
    )
    fig_area.update_yaxes(tickformat="~s")
    st.plotly_chart(fig_area, use_container_width=True)

with bubble_tab:
    st.subheader(f"Country snapshot for {selected_year}")
    st.write(
        "Use Play in the sidebar to move year by year. Bubble size reflects population, "
        "the x-axis is population on a log scale, and the y-axis is the poverty share."
    )

    bubble_cols = st.columns([2.2, 1])

    with bubble_cols[0]:
        if selected_year_df.empty:
            st.warning("No country data are available for this year and region filter.")
        else:
            bubble_df = selected_year_df.copy()
            bubble_df = bubble_df[bubble_df["Population"] > 0]
            fig_bubble = px.scatter(
                bubble_df,
                x="Population",
                y="Share of population in poverty ($3 a day)",
                size="Population",
                color="World region according to OWID",
                hover_name="Entity",
                size_max=55,
                log_x=True,
                opacity=0.8,
                labels={
                    "Population": "Population (log scale)",
                    "Share of population in poverty ($3 a day)": "Poverty share (%)",
                    "World region according to OWID": "Region",
                },
            )
            fig_bubble.update_traces(
                hovertemplate=(
                    "<b>%{hovertext}</b><br>Population: %{x:,.0f}<br>"
                    "Poverty share: %{y:.1f}%<extra></extra>"
                )
            )
            fig_bubble.update_layout(
                template="plotly_white",
                height=650,
                margin=dict(l=40, r=20, t=30, b=20),
                legend_title_text="",
            )
            fig_bubble.update_yaxes(range=[0, 100], ticksuffix="%")
            st.plotly_chart(fig_bubble, use_container_width=True)

    with bubble_cols[1]:
        st.markdown(f"**Top {top_n} countries in {selected_year}**")
        if selected_year_df.empty:
            st.info("No data available.")
        else:
            top_df = (
                selected_year_df.sort_values(
                    "Share of population in poverty ($3 a day)", ascending=False
                )[[
                    "Entity",
                    "Share of population in poverty ($3 a day)",
                    "Population",
                    "World region according to OWID",
                ]]
                .head(top_n)
                .rename(
                    columns={
                        "Entity": "Country",
                        "Share of population in poverty ($3 a day)": "Poverty share (%)",
                        "Population": "Population",
                        "World region according to OWID": "Region",
                    }
                )
            )
            top_df["Poverty share (%)"] = top_df["Poverty share (%)"].map(lambda x: f"{x:.2f}")
            top_df["Population"] = top_df["Population"].map(lambda x: f"{x:,.0f}")
            st.dataframe(top_df, use_container_width=True, hide_index=True)

st.divider()
st.markdown(
    "**Run locally:** `pip install -r requirements.txt` then `streamlit run app.py`"
)
