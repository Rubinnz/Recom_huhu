import pandas as pd
import streamlit as st

def _split_tokens(series: pd.Series) -> list[str]:
    tokens: set[str] = set()
    for v in series.dropna().astype(str):
        for p in v.split(","):
            t = p.strip()
            if t:
                tokens.add(t)
    return sorted(tokens)

def render_filter_bar(games: pd.DataFrame):
    all_genres = _split_tokens(games["genres"])
    all_platforms = _split_tokens(games["platforms"])
    all_titles = sorted(games["title"].dropna().unique().tolist())

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        selected_genres = st.multiselect("📂 Genres", options=all_genres, default=[], key="f_genres")
    with c2:
        selected_platforms = st.multiselect("💻 Platforms", options=all_platforms, default=[], key="f_platforms")
    with c3:
        selected_title = st.selectbox(
            "🔎 Search by game name",
            options=all_titles,
            index=None,
            key="f_title",
            placeholder="Select a game name...",
            help="Start typing or select a game name"
        )

    return selected_genres, selected_platforms, selected_title
    