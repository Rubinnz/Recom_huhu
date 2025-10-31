# home.py
import math, re
import streamlit as st
import pandas as pd
from data import get_dataset

PAGE_SIZE = 20  # số game mỗi trang

# --------- helpers ----------
TAG_RE = re.compile(r"<[^>]+>")

def strip_html(s: str) -> str:
    if not isinstance(s, str):
        return ""
    return TAG_RE.sub("", s).replace("&nbsp;", " ").strip()

def split_tokens(series: pd.Series) -> list[str]:
    """'Action, Adventure' -> ['Action','Adventure'] (unique, sorted)."""
    toks: set[str] = set()
    for v in series.dropna().astype(str):
        for p in v.split(","):
            t = p.strip()
            if t:
                toks.add(t)
    return sorted(toks)

def contains_any(cell: str, selected: list[str]) -> bool:
    """cell (chuỗi) có chứa ÍT NHẤT 1 token trong selected."""
    if not selected:
        return True
    if not isinstance(cell, str):
        return False
    s = {t.strip().lower() for t in cell.split(",")}
    return any(x.lower() in s for x in selected)

def scroll_to_top_once():
    if st.session_state.pop("_scroll_top", False):
        st.markdown("<script>window.scrollTo(0,0);</script>", unsafe_allow_html=True)

# --------- page ----------
def show_home():
    # ===== CSS =====
    st.markdown(
        """
        <style>
        .main-header {
            font-size: 2.2rem; font-weight: 800; color: white; text-align: center;
            padding: 1rem; margin: 0.5rem 0 1.25rem 0;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
        }
        .logout-btn button[kind="primary"] {
            background-color: #e74c3c !important;
            border: 1px solid #d24a3a !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            padding: 6px 12px !important;
        }
        .game-card { background:#1e1e1e; border-radius:12px; padding:12px; color:white; margin-bottom:16px; }
        .game-card h4 { margin: 0 0 6px 0; font-size: 1.1rem; color: #fff; }
        .game-meta { color:#cbd5e1; font-size:12px; margin-bottom:6px; }
        .pager { text-align:center; margin: 8px 0 0 0; }
        .page-chip { display:inline-block; padding:4px 10px; border:1px solid #e5e7eb; border-radius:999px; font-size:12px; color:#475569; background:#f8fafc; }
        .detail-box { background:#0f172a; color:#e2e8f0; border-radius:14px; padding:16px; border:1px solid #233056; }
        </style>
        """,
        unsafe_allow_html=True
    )

    # auto scroll-to-top nếu vừa nhấn chuyển trang
    scroll_to_top_once()

    # ===== Nút Logout góc phải =====
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

    # ===== Load dataset =====
    games, _ = get_dataset()

    # Chuẩn hoá cột cần dùng
    if not games.empty:
        for col in ("id", "title", "genres", "platforms", "cover_image", "description", "rating", "released", "game_link"):
            if col not in games.columns:
                games[col] = ""
        games["description_clean"] = games["description"].apply(strip_html)
        for c in ("title","genres","platforms","cover_image","game_link"):
            games[c] = games[c].fillna("").astype(str)

    # ===== Tabs =====
    tab1, tab2, tab3 = st.tabs(["📋 Tổng quan", "🎯 Gợi ý", "⚙️ Cài đặt"])

    # ---- Tab 1: Tổng quan = danh sách + bộ lọc + phân trang + CHI TIẾT ----
    with tab1:
        st.subheader("Danh sách game 🎮")

        if games.empty:
            st.warning("⚠️ Không có dữ liệu game.")
            return

        # ===== Panel chi tiết (nếu có chọn game) =====
        detail_id = st.session_state.get("detail_game_id")
        if detail_id:
            g = games[games["id"].astype(str) == str(detail_id)]
            if not g.empty:
                row = g.iloc[0]
                with st.container():
                    st.markdown("#### 📖 Chi tiết")
                    st.markdown('<div class="detail-box">', unsafe_allow_html=True)
                    cols = st.columns([2, 3])
                    with cols[0]:
                        img = row["cover_image"].strip()
                        if img:
                            st.image(img, width="stretch")
                        else:
                            st.image("https://via.placeholder.com/600x320.png?text=No+Image", width="stretch")
                    with cols[1]:
                        st.markdown(f"### {row['title'] or 'Unknown Game'}")
                        meta = []
                        if row["genres"]: meta.append(f"🎭 {row['genres']}")
                        if row["platforms"]: meta.append(f"💻 {row['platforms']}")
                        if row.get("rating", "") != "": meta.append(f"⭐ {row['rating']}")
                        if row.get("released", "") != "": meta.append(f"📅 {row['released']}")
                        if meta: st.markdown(" · ".join(meta))
                        desc = row["description_clean"] or "Chưa có mô tả."
                        st.markdown(desc)
                        if row["game_link"]:
                            st.link_button("🔗 Trang RAWG", row["game_link"], type="primary", width="content")
                    c1, c2 = st.columns([1,1])
                    with c1:
                        if st.button("Đóng", width="stretch", key="close_detail"):
                            st.session_state["detail_game_id"] = None
                            st.session_state["_scroll_top"] = True
                            st.rerun()
                    with c2:
                        st.empty()
                    st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("---")

        # ====== Bộ lọc ======
        all_genres = split_tokens(games["genres"])
        all_plats  = split_tokens(games["platforms"])

        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            selected_genres = st.multiselect("📂 Thể loại", options=all_genres, default=[], key="f_genres")
        with c2:
            selected_plats = st.multiselect("💻 Nền tảng", options=all_plats, default=[], key="f_plats")
        with c3:
            search_kw = st.text_input("🔎 Tìm theo tên game", value="", placeholder="nhập từ khoá…", key="f_kw")

        # reset trang khi filter đổi
        st.session_state.setdefault("games_page", 1)
        finger = (tuple(selected_genres), tuple(selected_plats), search_kw)
        if st.session_state.get("_filter_sig") != finger:
            st.session_state["_filter_sig"] = finger
            st.session_state["games_page"] = 1

        # ====== Lọc dữ liệu ======
        df = games.copy()
        if selected_genres:
            df = df[df["genres"].apply(lambda s: contains_any(s, selected_genres))]
        if selected_plats:
            df = df[df["platforms"].apply(lambda s: contains_any(s, selected_plats))]
        if search_kw:
            kw = search_kw.strip()
            if kw:
                df = df[df["title"].str.contains(kw, case=False, na=False)]

        # ====== Phân trang ======
        total_items = len(df)
        total_pages = max(1, math.ceil(total_items / PAGE_SIZE))
        page = max(1, min(st.session_state.get("games_page", 1), total_pages))
        start = (page - 1) * PAGE_SIZE
        end = start + PAGE_SIZE
        page_df = df.iloc[start:end]

        # ====== Render cards: 3 card/row ======
        n_cols = 3
        rows = [page_df.iloc[i:i+n_cols] for i in range(0, len(page_df), n_cols)]
        for row_df in rows:
            cols = st.columns(n_cols)
            for idx, (_, g) in enumerate(row_df.iterrows()):
                with cols[idx]:
                    st.markdown('<div class="game-card">', unsafe_allow_html=True)
                    img = g["cover_image"].strip()
                    if img:
                        st.image(img, width="stretch")
                    else:
                        st.image("https://via.placeholder.com/400x200.png?text=No+Image", width="stretch")
                    st.markdown(f"<h4>{g['title'] or 'Unknown Game'}</h4>", unsafe_allow_html=True)
                    meta = " · ".join(
                        m for m in [
                            f"🎭 {g['genres']}" if g['genres'] else "",
                            f"💻 {g['platforms']}" if g['platforms'] else ""
                        ] if m
                    )
                    if meta:
                        st.markdown(f"<div class='game-meta'>{meta}</div>", unsafe_allow_html=True)
                    desc = strip_html(g.get("description", "")) or "Chưa có mô tả."
                    st.caption(desc[:160] + ("..." if len(desc) > 160 else ""))

                    # >>> Nút xem chi tiết: set session_state và rerun
                    if st.button("📖 Xem chi tiết", key=f"detail_{g['id']}_{start+idx}", width="stretch"):
                        st.session_state["detail_game_id"] = g["id"]
                        st.session_state["_scroll_top"] = True
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

        # ====== Thanh chuyển trang (dưới cùng) ======
        st.markdown("")
        pc1, pc2, pc3 = st.columns([1, 2, 1])
        with pc2:
            colp1, colp2, colp3 = st.columns([1, 1, 1])
            with colp1:
                if st.button("« Trước", disabled=(page <= 1), width="stretch", key="prev_page"):
                    st.session_state["games_page"] = page - 1
                    st.session_state["_scroll_top"] = True
                    st.rerun()
            with colp2:
                st.markdown(f"<div class='pager'><span class='page-chip'>Trang {page}/{total_pages} — {total_items} game</span></div>", unsafe_allow_html=True)
            with colp3:
                if st.button("Sau »", disabled=(page >= total_pages), width="stretch", key="next_page"):
                    st.session_state["games_page"] = page + 1
                    st.session_state["_scroll_top"] = True
                    st.rerun()

    # ---- Tab 2/3: giữ đơn giản ----
    with tab2:
        st.subheader("🎯 Gợi ý trò chơi cho bạn (demo)")
        st.info("Sẽ gắn mô hình gợi ý ở đây sau.")
    with tab3:
        st.subheader("⚙️ Cài đặt tài khoản")
        st.text_input("Tên đăng nhập", value=username, disabled=True)
        st.text_input("Email", placeholder="email@example.com")
