import streamlit as st
import pandas as pd
import re

from .state import request_scroll_to_top, set_view

_TAG_RE = re.compile(r"<[^>]+>")

def _strip_html(s: str) -> str:
    if not isinstance(s, str):
        return ""
    return _TAG_RE.sub("", s).replace("&nbsp;", " ").strip()

def _get_game_row(games: pd.DataFrame, gid: str) -> pd.Series | None:
    if games is None or games.empty:
        return None
    row = games[games["id"].astype(str) == str(gid)]
    return row.iloc[0] if not row.empty else None

def render_detail_page(games: pd.DataFrame, gid: str):
    game = _get_game_row(games, gid)
    if game is None:
        st.warning("Game not found.")
        st.button("⬅️ Back", on_click=lambda: (set_view("list", None), request_scroll_to_top()))
        return

    c1, c2 = st.columns([1, 1])
    with c1:
        img = str(game.get("cover_image", "") or "").strip()
        st.image(img or "https://via.placeholder.com/600x340.png?text=No+Image", use_container_width=True)

    with c2:
        st.markdown(f"## {game.get('title','(No title)')}")
        meta = []
        if game.get("genres"):
            meta.append(f"🕹️ **Genres:** {game.get('genres')}")
        if game.get("platforms"):
            meta.append(f"💻 **Platforms:** {game.get('platforms')}")
        if game.get("released"):
            meta.append(f"📆 **Released:** {game.get('released')}")
        if game.get("rating"):
            meta.append(f"⭐ **Meta Rating:** {game.get('rating')}")
        for m in meta:
            st.markdown(m)
        link = str(game.get("game_link","") or "")
        if link:
            st.link_button("🔗 Game page", url=link, help="Open external link")

    st.markdown("---")
    st.markdown("#### Description")
    desc = _strip_html(game.get("description","") or "")    
    st.write(desc if desc else "_No description available._")

    st.markdown("---")
    st.button("⬅️ Back to list", on_click=lambda: (set_view("list", None), request_scroll_to_top()))
