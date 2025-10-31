import streamlit as st

# ====== Import các trang ======
from login import show_login
from register import show_register
from home import show_home
from forgot_password import show_forgot_password  # NEW

# ====== Page configuration ======
st.set_page_config(
    page_title="Video Game Recommender System",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ====== Global styles ======
st.markdown(
    """
<style>
  .main-header {
      font-size: 2.5rem;
      font-weight: bold;
      color: #2c3e50;
      text-align: center;
      padding: 1rem;
      background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
      color: white;
      border-radius: 10px;
      margin-bottom: 2rem;
  }
  .metric-card {
      background-color: #f8f9fa;
      padding: 1rem;
      border-radius: 8px;
      border-left: 4px solid #667eea;
  }
  .stTabs [data-baseweb="tab-list"] { gap: 24px; }
  .stTabs [data-baseweb="tab"] {
      height: 50px;
      padding: 0px 24px;
      background-color: #f0f2f6;
      border-radius: 8px 8px 0px 0px;
  }
  .stTabs [aria-selected="true"] {
      background-color: #667eea;
      color: white;
  }
</style>
""",
    unsafe_allow_html=True,
)

# ====== Initialize session state ======
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "email" not in st.session_state:
    st.session_state.email = ""
if "page" not in st.session_state:
    st.session_state.page = "login" 

# ====== Router ======
def main():
    if st.session_state.logged_in:
        st.session_state.page = "home"
        show_home()
        return

    page = st.session_state.page
    if page == "login":
        show_login()
    elif page == "register":
        show_register()
    elif page == "forgot":
        show_forgot_password()
    elif page == "home":
        st.session_state.page = "login"
        show_login()
    else:
        st.session_state.page = "login"
        show_login()

if __name__ == "__main__":
    main()
