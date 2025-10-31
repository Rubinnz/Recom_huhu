# home/__init__.py
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
    load_cf_model, load_cb_model,
    get_cf_recommendations, get_cb_recommendations,
    get_user_seen_items, top_popular,
    append_ratings_bulk, get_user_ids,   # <-- thêm 2 hàm này
)

CF_MODEL_PATH = "best_cf_model_SVD.pkl"
CB_MODEL_PATH = "best_cb_model_CB_Genres_Description.pkl"

_TAG_RE = re.compile(r"<[^>]+>")

def _strip_html(s: str) -> str:
    if not isinstance(s, str): return ""
    return _TAG_RE.sub("", s).replace("&nbsp;", " ").strip()

def _prepare_games_columns(games: pd.DataFrame) -> pd.DataFrame:
    need = ("id","title","genres","platforms","cover_image","description","rating","released","game_link")
    for c in need:
        if c not in games.columns: games[c] = ""
    games["description_clean"] = games["description"].apply(_strip_html)
    for c in ("title","genres","platforms","cover_image","game_link"):
        games[c] = games[c].fillna("").astype(str)

    # ➕ Thêm cột combined_text: gộp genres + description
    games["combined_text"] = (
        games["genres"].fillna("") + " " + games["description_clean"].fillna("")
    ).str.strip()
    return games


def show_home():
    st.markdown('<div id="top-anchor"></div>', unsafe_allow_html=True)

    inject_styles()
    sync_view_from_query()

    # ===== Logout =====
    _, top_right = st.columns([10, 2], gap="small")
    with top_right:
        st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
        if st.button("🚪 Đăng xuất", type="primary", width="stretch"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.page = "login"
            st.success("Đã đăng xuất thành công!")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ===== Header =====
    st.markdown('<div class="main-header">🎮 Video Game Recommender System</div>', unsafe_allow_html=True)
    username = st.session_state.get("username", "")
    st.markdown(f"### Chào mừng, **{username}**! 👋")
    st.markdown("---")

    # ===== Data =====
    games, ratings = get_dataset()
    if games.empty:
        st.warning("⚠️ Không có dữ liệu game.")
        scroll_to_top_after_render()
        return
    games = _prepare_games_columns(games)

    # ===== Routing =====
    view = get_view()
    if view == "detail":
        gid = st.session_state.get("detail_game_id") or st.query_params.get("gid")
        if isinstance(gid, list): gid = gid[0]
        render_detail_page(games, str(gid) if gid else "")
        scroll_to_top_after_render()
        return

    # ------------- VIEW DANH SÁCH -------------
    tab1, tab2, tab3 = st.tabs(["📋 Tổng quan", "🎯 Gợi ý", "⚙️ Cài đặt"])

    with tab1:
        st.subheader("Danh sách game 🎮")

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
                if st.button("« Trước", disabled=(page <= 1), width="stretch", key="prev_page"):
                    set_page(page - 1)
                    request_scroll_to_top()
                    st.rerun()
            with colp2:
                st.markdown(
                    f"<div class='pager'><span class='page-chip'>Trang {page}/{total_pages} — {total_items} game</span></div>",
                    unsafe_allow_html=True
                )
            with colp3:
                if st.button("Sau »", disabled=(page >= total_pages), width="stretch", key="next_page"):
                    set_page(page + 1)
                    request_scroll_to_top()
                    st.rerun()

    # --------- VIEW GỢI Ý ---------
    with tab2:
        st.subheader("🎯 Gợi ý trò chơi cho bạn")

        model_choice = st.radio(
            "Chọn mô hình gợi ý:",
            ["Collaborative Filtering (SVD)", "Content-Based (Genres)"],
            horizontal=True
        )
        topn = st.slider("Số lượng gợi ý", min_value=3, max_value=30, value=5, step=1)

        cf_model = cb_model = None
        cb_load_err = None

        if model_choice.startswith("Collaborative"):
            try:
                cf_model = load_cf_model(CF_MODEL_PATH)
            except Exception as e:
                st.error(f"Không load được CF model: {e}")
        else:
            try:
                cb_model = load_cb_model(CB_MODEL_PATH)
            except Exception as e:
                cb_load_err = str(e)
                st.warning("Không load được CB model. Sẽ dùng fallback TF-IDF trên 'genres'.")

        # ===== CF mode =====
        if model_choice.startswith("Collaborative"):
            if cf_model is None:
                st.info("Chưa có CF model để chạy. Kiểm tra file .pkl hoặc cách lưu model (joblib/pickle).")
            else:
                st.caption("Mô hình: **SVD Collaborative Filtering** — đề xuất dựa trên cộng đồng người dùng tương tự.")

                # Danh sách user_id từ file ratings (tự phát hiện schema)
                user_opts = get_user_ids()

                default_user = st.session_state.get("username", "")
                if default_user not in user_opts and user_opts:
                    default_user = user_opts[0]

                selected_user = st.selectbox(
                    "Chọn user để gợi ý (CF):",
                    options=user_opts if user_opts else ([default_user] if default_user else []),
                    index=(user_opts.index(default_user) if default_user and default_user in user_opts else 0) if (user_opts or default_user) else 0,
                    help="CF cần user có lịch sử rating trong game_ratings.csv."
                )
                manual_user = st.text_input("Hoặc nhập user_id thủ công:", value=selected_user or "")
                target_user = (manual_user or "").strip() or selected_user

                if not target_user:
                    st.warning("Hãy chọn hoặc nhập một user hợp lệ.")
                else:
                    seen = get_user_seen_items(ratings, target_user) if ratings is not None else set()
                    if len(seen) == 0:
                        st.info(f"User **{target_user}** chưa có rating → cold-start: chất lượng gợi ý có thể thấp.")

                        # --- Warm-up nhanh: chọn vài game và lưu rating ---
                        with st.expander("🔥 Thêm 3–5 game bạn thích để warm-up CF"):
                            colw1, colw2 = st.columns([2,1])
                            with colw1:
                                seed_games = st.multiselect(
                                    "Chọn game đã chơi & thích:",
                                    options=sorted(games["title"].dropna().unique().tolist()),
                                    max_selections=5
                                )
                            with colw2:
                                seed_rating = st.slider("Điểm chung", 1.0, 5.0, 4.5, 0.5)

                            if st.button("💾 Lưu rating & tạo gợi ý", type="primary"):
                                if not seed_games:
                                    st.warning("Hãy chọn ít nhất 1 game.")
                                else:
                                    ids = games.loc[games["title"].isin(seed_games), "id"].astype(str).tolist()
                                    new_ratings = append_ratings_bulk(user_id=target_user, item_ids=ids, rating=seed_rating)
                                    # Cập nhật biến ratings hiện tại để dùng ngay
                                    ratings = new_ratings
                                    st.success(f"Đã lưu {len(ids)} rating cho **{target_user}**. Đang gợi ý lại…")
                                    st.rerun()

                        # --- Fallback tạm thời: Popular & Content-Based ---
                        st.markdown("##### Hoặc xem gợi ý tạm thời")
                        pop_df = top_popular(games, ratings, topn=topn)
                        if pop_df is not None and not pop_df.empty:
                            st.write("**Phổ biến hiện nay**")
                            render_game_cards(pop_df, start_index=0, key_prefix="rec_pop_")

                        with st.expander("Content-Based tạm thời (chọn 1 game 'seed')"):
                            seed_cb = st.selectbox(
                                "Chọn game 'seed' (CB):",
                                options=sorted(games["title"].dropna().unique().tolist()),
                                key="cb_temp_seed"
                            )
                            if seed_cb:
                                rec_cb = get_cb_recommendations(cb_model, games, seed_title=seed_cb, topn=topn)
                                if rec_cb is not None and not rec_cb.empty:
                                    render_game_cards(rec_cb, start_index=0, key_prefix="rec_cb_tmp_")

                    else:
                        # User đã có rating → chạy CF bình thường
                        rec_df = get_cf_recommendations(cf_model, target_user, games, ratings, topn=topn)
                        if rec_df is None or rec_df.empty:
                            st.info("Chưa có gợi ý phù hợp (thiếu dữ liệu). Bạn có thể warm-up thêm hoặc dùng CB.")
                        else:
                            render_game_cards(rec_df, start_index=0, key_prefix="rec_")

        # ===== CB mode =====
        else:
            st.caption("Mô hình: **Content-Based (Genres + Description)** — đề xuất dựa trên thể loại và mô tả.")
            seed = st.selectbox(
                "Chọn 1 game bạn thích làm 'seed':",
                options=sorted(games["title"].dropna().unique().tolist())
            )
            if seed:
                rec_df = get_cb_recommendations(
                    cb_model, games,
                    seed_title=seed,
                    topn=topn,
                    text_col="combined_text"  # 👈 Dùng genres + description
                )
                if rec_df is None or rec_df.empty:
                    if cb_load_err:
                        st.info("Fallback TF-IDF cũng chưa gợi ý được. Thử seed khác hoặc kiểm tra dữ liệu.")
                    else:
                        st.info("Chưa tìm được game tương tự. Mời thử game khác.")
                else:
                    render_game_cards(rec_df, start_index=0, key_prefix="rec_")


    with tab3:
        render_account_tab(st.session_state.get("username",""))

    scroll_to_top_after_render()
