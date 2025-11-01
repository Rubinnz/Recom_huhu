# home/filters.py
import pandas as pd
import streamlit as st

def _split_tokens(series: pd.Series) -> list[str]:
    toks: set[str] = set()
    for v in series.dropna().astype(str):
        for p in v.split(","):
            t = p.strip()
            if t:
                toks.add(t)
    return sorted(toks)

def render_filter_bar(games: pd.DataFrame):
    all_genres = _split_tokens(games["genres"])
    all_plats  = _split_tokens(games["platforms"])

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        selected_genres = st.multiselect("📂 Genres", options=all_genres, default=[], key="f_genres")
    with c2:
        selected_plats = st.multiselect("💻 Platforms", options=all_plats, default=[], key="f_plats")
    with c3:
        search_kw = st.text_input("🔎 Search by game name", value="", placeholder="enter keyword…", key="f_kw")

    return selected_genres, selected_plats, search_kw
