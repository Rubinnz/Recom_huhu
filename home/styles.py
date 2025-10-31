# home/styles.py
import streamlit as st

CSS = """
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
.page-chip {
  display:inline-block; padding:4px 10px; border:1px solid #e5e7eb;
  border-radius:999px; font-size:12px; color:#475569; background:#f8fafc;
}
.detail-box {
  background:#0f172a; color:#e2e8f0; border-radius:14px; padding:16px; border:1px solid #233056;
}
"""

def inject_styles():
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
