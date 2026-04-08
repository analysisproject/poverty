import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Poverty Animation Dashboard", layout="wide")

# =========================
# 데이터 로드
# =========================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

share_file = DATA_DIR / "share-of-population-in-extreme-poverty.csv"
proj_file = DATA_DIR / "projections-extreme-poverty-wb.csv"

@st.cache_data
def load_data():
    df_share = pd.read_csv(share_file)
    df_proj = pd.read_csv(proj_file)
    return df_share, df_proj

df_share, df_proj = load_data()

# =========================
# 컬럼 정리
# =========================
share_col = "Share of population in poverty ($3 a day)"
pop_col = "Population"

df_share["Year"] = pd.to_numeric(df_share["Year"], errors="coerce")
df_share[share_col] = pd.to_numeric(df_share[share_col], errors="coerce")
df_share[pop_col] = pd.to_numeric(df_share[pop_col], errors="coerce")

df_share = df_share.dropna(subset=["Entity", "Year", share_col, pop_col])

# 국가 코드 있는 일반 국가만 우선 사용
if "Code" in df_share.columns:
    df_share = df_share[df_share["Code"].notna()].copy()

# 너무 작은 나라까지 다 넣으면 버블이 과밀할 수 있으니 필터 옵션 제공
min_pop = st.sidebar.slider("Minimum population", 0, 50_000_000, 1_000_000, step=500_000)
df_anim = df_share[df_share[pop_col] >= min_pop].copy()

# region 비슷한 구분이 없으면 Entity 그대로 색상 쓰면 너무 복잡하므로
# 기본은 단색 + hover 강화
# 만약 Region 컬럼이 있다면 그걸 사용
color_col = "Region" if "Region" in df_anim.columns else None

st.title("Extreme Poverty Dashboard")
st.caption("Play 버튼을 누르면 연도별로 버블이 자연스럽게 이동합니다.")

# =========================
# 1. Animated Bubble Chart
# =========================
st.subheader("1) Animated bubble chart by year")

fig_anim = px.scatter(
    df_anim.sort_values("Year"),
    x=share_col,
    y=pop_col,
    animation_frame="Year",
    animation_group="Entity",
    size=pop_col,
    hover_name="Entity",
    color=color_col if color_col else None,
    size_max=60,
    log_y=True,
    range_x=[0, min(100, df_anim[share_col].max() + 5)],
    range_y=[max(1e5, df_anim[pop_col].min()), df_anim[pop_col].max() * 1.2],
    labels={
        share_col: "Extreme poverty share (%)",
        pop_col: "Population"
    },
    title="Countries over time: poverty rate vs population"
)

fig_anim.update_traces(
    marker=dict(opacity=0.75, line=dict(width=0.5, color="white")),
    selector=dict(mode="markers")
)

fig_anim.update_layout(
    template="plotly_white",
    height=750,
    xaxis=dict(title="Share of population in poverty (%)"),
    yaxis=dict(title="Population (log scale)"),
    legend_title_text="",
    margin=dict(l=40, r=40, t=80, b=40)
)

# 애니메이션 속도 조정
fig_anim.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 500
fig_anim.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 300
fig_anim.layout.updatemenus[0].buttons[0].args[1]["fromcurrent"] = True

st.plotly_chart(fig_anim, use_container_width=True)

# =========================
# 2. 선택 국가 추이
# =========================
st.subheader("2) Country trend")

default_countries = ["India", "Nigeria", "Ethiopia", "DR Congo", "Bangladesh"]
available = sorted(df_share["Entity"].unique().tolist())
default_selected = [c for c in default_countries if c in available][:5]

selected_countries = st.multiselect(
    "Select countries",
    options=available,
    default=default_selected
)

if selected_countries:
    plot_df = df_share[df_share["Entity"].isin(selected_countries)].copy()

    fig_line = px.line(
        plot_df,
        x="Year",
        y=share_col,
        color="Entity",
        markers=True,
        labels={"Year": "Year", share_col: "Extreme poverty share (%)"},
        title="Country trends in extreme poverty"
    )

    fig_line.update_layout(
        template="plotly_white",
        height=500,
        legend_title_text=""
    )
    st.plotly_chart(fig_line, use_container_width=True)

# =========================
# 3. 특정 연도 스냅샷
# =========================
st.subheader("3) Snapshot by year")

year_list = sorted(df_share["Year"].dropna().unique().astype(int).tolist())
selected_year = st.slider(
    "Choose a year for snapshot",
    min_value=min(year_list),
    max_value=max(year_list),
    value=min(year_list),
    step=1
)

snap_df = df_share[df_share["Year"] == selected_year].copy()
snap_df = snap_df.sort_values(share_col, ascending=False).head(20)

fig_bar = px.bar(
    snap_df,
    x=share_col,
    y="Entity",
    orientation="h",
    labels={share_col: "Extreme poverty share (%)", "Entity": ""},
    title=f"Top 20 countries by poverty share in {selected_year}"
)

fig_bar.update_layout(
    template="plotly_white",
    height=700,
    yaxis={"categoryorder": "total ascending"}
)

st.plotly_chart(fig_bar, use_container_width=True)
