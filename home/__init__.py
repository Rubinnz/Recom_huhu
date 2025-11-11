import re
import pandas as pd
import streamlit as st
from data import get_dataset
from .styles import inject_styles
from .state import (
    PAGE_SIZE, get_current_page, set_page,
    reset_page_if_filter_changed, request_scroll_to_top,
    scroll_to_top_after_render, get_view, set_view, sync_view_from_query
)
from .filters import render_filter_bar
from .cards import filter_games, render_game_cards
from .detail import render_detail_page
from utils.recommender_utils import (
    load_hybrid_model, hybrid_top_recommendations,
    hybrid_grouped_recommendations, played_game_ids
)

HYBRID_PATH = "hybrid_model.pkl"
_TAG_RE = re.compile(r"<[^>]+>")

def _strip_html(s: str) -> str:
    if not isinstance(s, str):
        return ""
    return _TAG_RE.sub("", s).replace("&nbsp;", " ").strip()

def _prepare_games_columns(games: pd.DataFrame) -> pd.DataFrame:
    need = ("id", "title", "genres", "platforms", "cover_image", "description")
    cols = [c for c in need if c in games.columns]
    df = games.loc[:, cols].copy()
    if "description" in df.columns:
        df["description"] = df["description"].astype(str).map(_strip_html)
    df["id"] = df["id"].astype(str)
    df["title"] = df.get("title", "").astype(str)
    return df

def _load_games() -> pd.DataFrame:
    ds = get_dataset()
    games = ds["games"] if isinstance(ds, dict) and "games" in ds else ds
    if not isinstance(games, pd.DataFrame):
        games = pd.DataFrame()
    return _prepare_games_columns(games)

def _load_hybrid():
    try:
        return load_hybrid_model(HYBRID_PATH)
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None

def _merge_recs(recs: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    if "title" in recs.columns and "title" in games.columns:
        merged = recs.merge(games, on="title", how="left")
        if "id_x" in merged.columns and "id_y" in merged.columns:
            merged["id"] = merged["id_y"].fillna(merged["id_x"])
            merged = merged.drop(columns=["id_x", "id_y"])
        return merged
    if "id" in recs.columns and "id" in games.columns:
        return recs.merge(games, on="id", how="left")
    if "game_id" in recs.columns:
        tmp = recs.rename(columns={"game_id": "id"})
        tmp["id"] = tmp["id"].astype(str)
        return tmp.merge(games, on="id", how="left")
    return pd.DataFrame(columns=list(games.columns))

def show_home():
    inject_styles()
    st.markdown("<h1 class='main-header'>🎮 Video Game Recommender System</h1>", unsafe_allow_html=True)
    sync_view_from_query()
    games = _load_games()
    if games.empty:
        st.error("No game data available.")
        return

    gid = st.query_params.get("id", None)
    if gid:
        if isinstance(gid, list):
            gid = gid[0]
        render_detail_page(games, str(gid))
        scroll_to_top_after_render()
        return

    tab1, tab2 = st.tabs(["📋 Game List", "🎯 Personalized Recommendations"])

    with tab1:
        st.subheader("All Games 🎮")
        sel_genres, sel_plats, search_kw = render_filter_bar(games)
        reset_page_if_filter_changed((tuple(sel_genres), tuple(sel_plats), search_kw))
        df = filter_games(games, sel_genres, sel_plats, search_kw)
        total_items = len(df)
        total_pages = max(1, (total_items + PAGE_SIZE - 1) // PAGE_SIZE)
        page = get_current_page(total_pages)
        start = (page - 1) * PAGE_SIZE
        end = start + PAGE_SIZE
        render_game_cards(df.iloc[start:end], start)
        st.markdown("<div class='pager'>", unsafe_allow_html=True)
        sp1, col1, col2, col3, sp2 = st.columns([1.5, 1, 0.4, 1, 1.5], gap="small")
        with col1:
            if st.button("⬅️ Previous Page", disabled=page <= 1, key="prev_btn", use_container_width=True):
                set_page(page - 1)
                request_scroll_to_top()
        with col2:
            st.markdown(
                f"<p style='text-align:center; font-weight:600; font-size:1rem;'>Page {page}/{total_pages}</p>",
                unsafe_allow_html=True
            )
        with col3:
            if st.button("Next Page ➡️", disabled=page >= total_pages, key="next_btn", use_container_width=True):
                set_page(page + 1)
                request_scroll_to_top()
        st.markdown("</div>", unsafe_allow_html=True)
        
    with tab2:
        st.subheader("Personalized Game Recommendations")
        model = _load_hybrid()
        if model is None:
            st.warning("⚠️ Model not found or failed to load.")
            return
        user_list = []
        if hasattr(model, "all_users"):
            user_list = sorted(list(map(str, model.all_users)))
        if not user_list:
            st.warning("⚠️ Không tìm thấy danh sách user từ mô hình — sẽ dùng chế độ cold-start.")
            user_id = None
        else:
            user_options = ["-- New User (Cold Start) --"] + user_list
            user_choice = st.selectbox("👤 Chọn user_id", user_options, index=0)
            if user_choice == "-- New User (Cold Start) --":
                user_id = None
                st.info("🆕 Đang dùng chế độ cold-start (người dùng mới).")
            else:
                user_id = user_choice
                st.success(f"✅ Đã chọn user: {user_id}")
        k = st.number_input("Number of recommendations", min_value=5, max_value=50, value=10, step=1)
        if st.button("Get Recommendations", use_container_width=True):
            with st.spinner("Getting recommendations..."):
                try:
                    recs = hybrid_top_recommendations(model, user_id=user_id if user_id else None, n=int(k))
                    st.success(f"✅ Got {len(recs)} recommendations")
                    if not recs.empty:
                        merged = _merge_recs(recs, games)
                        if not merged.empty:
                            st.write(f"**Top {len(merged)} recommendations for {user_id or 'New User'}:**")
                            render_game_cards(merged, 0)
                        else:
                            st.info("No suitable recommendations found.")
                    else:
                        st.info("No recommendations found.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        st.markdown("---")
        st.caption("Recommendations by Theme Group")
        try:
            grouped = hybrid_grouped_recommendations(model, user_id, per_seed=4)
        except Exception as e:
            st.error(f"Error getting grouped recommendations: {e}")
            grouped = {}
        if isinstance(grouped, dict) and grouped:
            for gtitle, df in grouped.items():
                merged = _merge_recs(df, games)
                if not merged.empty:
                    st.markdown(f"**{gtitle}**")
                    render_game_cards(merged, 0)
        else:
            st.info("No grouped recommendations available.")
