import re
import pandas as pd
import streamlit as st
from data import get_dataset

from .styles import inject_styles
from .state import (
    PAGE_SIZE, get_current_page, set_page, reset_page_if_filter_changed,
    request_scroll_to_top, scroll_to_top_after_render,
    get_view, set_view, sync_view_from_query
)
from .filters import render_filter_bar
from .cards import filter_games, render_game_cards
from .detail import render_detail_page
from .account import render_account_tab

from utils.recommender_utils import (
    load_cb_model,
    get_cb_recommendations,
)

CB_MODEL_PATH = "best_cb_model_CB_Genres_Description.pkl"

_TAG_RE = re.compile(r"<[^>]+>")

def _strip_html(s: str) -> str:
    if not isinstance(s, str):
        return ""
    return _TAG_RE.sub("", s).replace("&nbsp;", " ").strip()

def _prepare_games_columns(games: pd.DataFrame) -> pd.DataFrame:
    need = ("id", "title", "genres", "platforms", "cover_image", "description", "rating", "released", "game_link")
    for c in need:
        if c not in games.columns:
            games[c] = ""
    games["description_clean"] = games["description"].apply(_strip_html)
    for c in ("title", "genres", "platforms", "cover_image", "game_link"):
        games[c] = games[c].fillna("").astype(str)
    games["combined_text"] = (
        games["genres"].fillna("") + " " + games["description_clean"].fillna("")
    ).str.strip()
    return games

def show_home():
    st.markdown('<div id="top-anchor"></div>', unsafe_allow_html=True)

    inject_styles()
    sync_view_from_query()

    _, top_right = st.columns([10, 2], gap="small")
    with top_right:
        st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
        if st.button("🚪 Log out", type="primary", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.page = "login"
            st.success("Successfully logged out!")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="main-header">🎮 Video Game Recommender System</div>', unsafe_allow_html=True)
    username = st.session_state.get("username", "")
    st.markdown(f"### Welcome, **{username}**! 👋")
    st.markdown("---")

    games = get_dataset()
    if games.empty:
        st.warning("⚠️ No game data found.")
        scroll_to_top_after_render()
        return
    games = _prepare_games_columns(games)

    view = get_view()
    if view == "detail":
        gid = st.session_state.get("detail_game_id") or st.query_params.get("gid")
        if isinstance(gid, list):
            gid = gid[0]
        render_detail_page(games, str(gid) if gid else "")
        scroll_to_top_after_render()
        return

    tab1, tab2, tab3 = st.tabs(["📋 Overview", "🎯 Favorites", "⚙️ Settings"])

    with tab1:
        st.subheader("Game list 🎮")

        sel_genres, sel_plats, search_kw = render_filter_bar(games)
        reset_page_if_filter_changed((tuple(sel_genres), tuple(sel_plats), search_kw))

        df = filter_games(games, sel_genres, sel_plats, search_kw)

        total_items = len(df)
        total_pages = max(1, (total_items + PAGE_SIZE - 1) // PAGE_SIZE)
        page = get_current_page(total_pages)
        start = (page - 1) * PAGE_SIZE
        end = start + PAGE_SIZE
        page_df = df.iloc[start:end]

        render_game_cards(page_df, start)

        st.markdown("")
        pc1, pc2, pc3 = st.columns([1, 2, 1])
        with pc2:
            colp1, colp2, colp3 = st.columns([1, 1, 1])
            with colp1:
                if st.button("« Previous", disabled=(page <= 1), use_container_width=True, key="prev_page"):
                    set_page(page - 1)
                    request_scroll_to_top()
                    st.rerun()
            with colp2:
                st.markdown(
                    f"<div class='pager'><span class='page-chip'>Page {page}/{total_pages} — {total_items} games</span></div>",
                    unsafe_allow_html=True
                )
            with colp3:
                if st.button("Next »", disabled=(page >= total_pages), use_container_width=True, key="next_page"):
                    set_page(page + 1)
                    request_scroll_to_top()
                    st.rerun()

    with tab2:
        st.subheader("🎯 Choose your favorite game")
        topn = st.slider("Number of recommendations", min_value=3, max_value=30, value=5, step=1)

        cb_model = None
        cb_load_err = None
        try:
            cb_model = load_cb_model(CB_MODEL_PATH)
        except Exception as e:
            cb_load_err = str(e)
            st.warning("Unable to load CB model. Using fallback TF-IDF on 'genres'.")

        seed = st.selectbox(
            "Choose a game you like to get recommendations:",
            options=sorted(games["title"].dropna().unique().tolist())
        )
        if seed:
            rec_df = get_cb_recommendations(
                cb_model, games,
                seed_title=seed,
                topn=topn,
                text_col="combined_text"
            )
            if rec_df is None or rec_df.empty:
                if cb_load_err:
                    st.info("Fallback TF-IDF also failed to recommend. Try another seed or check the dataset.")
                else:
                    st.info("Not found. Try another game.")
            else:
                render_game_cards(rec_df, start_index=0, key_prefix="rec_")

    with tab3:
        render_account_tab(st.session_state.get("username", ""))

    scroll_to_top_after_render()
