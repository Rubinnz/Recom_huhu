# home/cards.py
import re
import pandas as pd
import streamlit as st
from .state import request_scroll_to_top, set_view

_TAG_RE = re.compile(r"<[^>]+>")

def _strip_html(s: str) -> str:
    if not isinstance(s, str):
        return ""
    return _TAG_RE.sub("", s).replace("&nbsp;", " ").strip()

def _contains_any(cell: str, selected: list[str]) -> bool:
    if not selected: return True
    if not isinstance(cell, str): return False
    s = {t.strip().lower() for t in cell.split(",")}
    return any(x.lower() in s for x in selected)

def filter_games(games: pd.DataFrame, genres: list[str], plats: list[str], kw: str) -> pd.DataFrame:
    df = games.copy()
    if genres:
        df = df[df["genres"].apply(lambda s: _contains_any(s, genres))]
    if plats:
        df = df[df["platforms"].apply(lambda s: _contains_any(s, plats))]
    kw = (kw or "").strip()
    if kw:
        df = df[df["title"].str.contains(kw, case=False, na=False)]
    return df

def render_game_cards(page_df: pd.DataFrame, start_index: int, key_prefix: str = ""):
    n_cols = 3
    rows = [page_df.iloc[i:i+n_cols] for i in range(0, len(page_df), n_cols)]
    for row in rows:
        cols = st.columns(n_cols)
        for idx, (row_idx, g) in enumerate(row.iterrows()):
            with cols[idx]:
                st.markdown('<div class="game-card">', unsafe_allow_html=True)
                img = str(g.get("cover_image", "")).strip()
                if img:
                    st.image(img, width="stretch")
                else:
                    st.image("https://via.placeholder.com/400x200.png?text=No+Image", width="stretch")

                title = g.get("title") or "Unknown Game"
                st.markdown(f"<h4>{title}</h4>", unsafe_allow_html=True)

                meta = " · ".join(
                    m for m in [
                        f"🕹️ {g.get('genres')}" if g.get("genres") else "",
                        f"💻 {g.get('platforms')}" if g.get("platforms") else ""
                    ] if m
                )
                if meta:
                    st.markdown(f"<div class='game-meta'>{meta}</div>", unsafe_allow_html=True)

                desc = _strip_html(g.get("description", "")) or "Chưa có mô tả."
                st.caption(desc[:160] + ("..." if len(desc) > 160 else ""))

                # Key duy nhất để tránh StreamlitDuplicateElementKey
                safe_id = str(g.get("id", "NA"))
                button_key = f"{key_prefix}detail_{start_index}_{idx}_{row_idx}_{safe_id}"

                if st.button("📖 Xem chi tiết", key=button_key, width="stretch"):
                    set_view("detail", str(g["id"]))
                    request_scroll_to_top()
                    st.rerun()

                st.markdown('</div>', unsafe_allow_html=True)
