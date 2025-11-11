import streamlit as st

CSS = """
.main-header {
  font-size: 2.6rem;
  font-weight: 800;
  text-align: center;
  margin: 1.5rem 0 2rem 0;
  padding: 1rem;
  border-radius: 16px;
  background: linear-gradient(90deg, #FF00A1, #7904EB);
  color: #FFFFFF !important;
  text-shadow: 0 0 25px rgba(255,255,255,0.6);
  box-shadow: 0 0 25px rgba(121,4,235,0.25);
}a

.logout-btn button[kind="primary"] {
  background-color: #e74c3c !important;
  border: 1px solid #d24a3a !important;
  color: #ffffff !important;
  border-radius: 8px !important;
  padding: 6px 12px !important;
}

.game-card {
  background:#1e1e1e;
  border-radius:12px;
  padding:12px;
  color:white;
  margin-bottom:16px;
}
.game-card h4 {
  margin: 0 0 6px 0;
  font-size: 1.1rem;
  color: #fff;
}
.game-meta {
  color:#cbd5e1;
  font-size:12px;
  margin-bottom:6px;
}
.pager {
  text-align:center;
  margin: 8px 0 0 0;
}
.page-chip {
  display:inline-block;
  padding:4px 10px;
  border:1px solid #e5e7eb;
  border-radius:999px;
  font-size:12px;
  color:#475569;
  background:#f8fafc;
}
.detail-box {
  background:#0f172a;
  color:#e2e8f0;
  border-radius:14px;
  padding:16px;
  border:1px solid #233056;
}
.pager {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1.5rem;
  margin-top: 1.2rem;
}

.stButton > button[kind="primary"], .stButton > button.page-btn {
  background: linear-gradient(90deg, #FF00A1, #7904EB);
  color: white !important;
  font-weight: 600;
  border: none;
  border-radius: 12px;
  padding: 0.45rem 1.4rem;
  font-size: 0.9rem;
  transition: all 0.25s ease;
  box-shadow: 0 0 12px rgba(121,4,235,0.25);
}

.stButton > button[kind="primary"]:hover, .stButton > button.page-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 0 16px rgba(255,0,161,0.35);
  background: linear-gradient(90deg, #FE76FF, #8A2BE2);
}

"""

def inject_styles():
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
  