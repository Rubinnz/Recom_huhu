import os
import time
import streamlit as st

PAGE_SIZE = 21

def get_view() -> str:
    qp = st.query_params
    if "v" in qp:
        v = qp.get("v")
        if isinstance(v, list):
            v = v[0]
        return v or st.session_state.get("view", "list")
    return st.session_state.get("view", "list")

def set_view(view: str, game_id: str | None = None):
    st.session_state["view"] = view
    if game_id is not None:
        st.session_state["detail_game_id"] = str(game_id)
        st.query_params.update({"v": "detail", "gid": str(game_id)})
    else:
        st.session_state["detail_game_id"] = None
        st.query_params.update({"v": "list"})
        if "gid" in st.query_params:
            del st.query_params["gid"]

def sync_view_from_query():
    qp = st.query_params
    if "v" in qp:
        v = qp.get("v")
        if isinstance(v, list):
            v = v[0]
        st.session_state["view"] = v
    if "gid" in qp:
        gid = qp.get("gid")
        if isinstance(gid, list):
            gid = gid[0]
        st.session_state["detail_game_id"] = gid

def request_scroll_to_top():
    st.session_state["_scroll_top"] = True

def scroll_to_top_after_render():
    if st.session_state.get("_scroll_top", False):
        st.markdown(
            """
            <script>
            (function(){
              function goTop(){
                try{
                  var el = document.getElementById('top-anchor');
                  if (el && el.scrollIntoView) el.scrollIntoView({behavior:'instant', block:'start'});
                  else window.scrollTo(0,0);
                }catch(e){ window.scrollTo(0,0); }
              }
              setTimeout(goTop, 0);
              setTimeout(goTop, 60);
            })();
            </script>
            """,
            unsafe_allow_html=True
        )
        st.session_state["_scroll_top"] = False

def get_current_page(total_pages: int) -> int:
    page = max(1, min(st.session_state.get("games_page", 1), max(1, total_pages)))
    return page

def set_page(page: int):
    st.session_state["games_page"] = max(1, page)

def reset_page_if_filter_changed(signature: tuple):
    if st.session_state.get("_filter_sig") != signature:
        st.session_state["_filter_sig"] = signature
        st.session_state["games_page"] = 1
        request_scroll_to_top()
