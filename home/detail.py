# home/detail.py
import streamlit as st
import pandas as pd
import re

from .state import request_scroll_to_top, set_view
from utils.recommender_utils import (
    get_existing_rating, upsert_user_rating, remove_user_rating
)

_TAG_RE = re.compile(r"<[^>]+>")

def _strip_html(s: str) -> str:
    if not isinstance(s, str): return ""
    return _TAG_RE.sub("", s).replace("&nbsp;", " ").strip()

def _get_game_row(games: pd.DataFrame, gid: str) -> pd.Series | None:
    if games is None or games.empty:
        return None
    row = games[games["id"].astype(str) == str(gid)]
    return row.iloc[0] if not row.empty else None

def render_detail_page(games: pd.DataFrame, gid: str):
    game = _get_game_row(games, gid)
    if game is None:
        st.warning("Không tìm thấy game.")
        st.button("⬅️ Quay lại", on_click=lambda: (set_view("list", None), request_scroll_to_top()))
        return

    # ==== Header ====
    c1, c2 = st.columns([1, 1])
    with c1:
        img = str(game.get("cover_image", "") or "").strip()
        st.image(img or "https://via.placeholder.com/600x340.png?text=No+Image", use_container_width=True)

    with c2:
        st.markdown(f"## {game.get('title','(No title)')}")
        meta = []
        if game.get("genres"): meta.append(f"🕹️ **Genres:** {game.get('genres')}")
        if game.get("platforms"): meta.append(f"💻 **Platforms:** {game.get('platforms')}")
        if game.get("released"): meta.append(f"📆 **Released:** {game.get('released')}")
        if game.get("rating"): meta.append(f"⭐ **Meta Rating:** {game.get('rating')}")
        for m in meta: st.markdown(m)
        link = str(game.get("game_link","") or "")
        if link:
            st.link_button("🔗 Trang game", url=link, help="Mở link ngoài")

    st.markdown("---")
    st.markdown("#### Mô tả")
    desc = _strip_html(game.get("description","") or "")
    st.write(desc if desc else "_Chưa có mô tả._")

    st.markdown("---")

    # ==== Rating của người dùng ====
    st.markdown("### ⭐ Đánh giá của bạn")
    default_user = st.session_state.get("username", "")
    user_id = st.text_input("User ID để lưu rating:", value=default_user, placeholder="nhập user_id…")
    if not user_id:
        st.info("Nhập `user_id` để lưu/đổi rating cho game này.")
    else:
        current = get_existing_rating(user_id, str(game["id"]))
        st.caption(f"ID game: `{game['id']}` • User: `{user_id}`")
        rating_val = st.slider("Điểm của bạn (1–5):", 1.0, 5.0, float(current) if current is not None else 4.5, 0.5)
        colr1, colr2, _ = st.columns([1,1,2])
        with colr1:
            if st.button("💾 Lưu/Cập nhật", type="primary", use_container_width=True):
                upsert_user_rating(user_id, str(game["id"]), float(rating_val))
                st.success("Đã lưu rating. Trang sẽ tải lại để cập nhật.")
                st.rerun()
        with colr2:
            if st.button("🗑️ Xoá rating", use_container_width=True, disabled=(current is None)):
                remove_user_rating(user_id, str(game["id"]))
                st.success("Đã xoá rating. Trang sẽ tải lại để cập nhật.")
                st.rerun()

    st.markdown("---")
    st.button("⬅️ Quay lại danh sách", on_click=lambda: (set_view("list", None), request_scroll_to_top()))
