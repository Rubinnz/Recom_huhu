import streamlit as st
from login import show_login
from register import show_register
from home import show_home
from forgot_password import show_forgot_password

st.set_page_config(
    page_title="Video Game Recommender System",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
html, body, [class*="css"] {
    background-color: #F8F9FF;
    color: #1A1A1A;
    font-family: 'Poppins', 'Segoe UI', sans-serif;
}

/* Header */
.main-header {
    font-size: 2.8rem;
    font-weight: 700;
    text-align: center;
    padding: 1.2rem;
    margin: 2rem 0;
    border-radius: 18px;
    background: linear-gradient(90deg, #FF00A1, #7904EB);
    color: #FFFFFF;
    text-shadow: 0 0 25px rgba(255,0,161,0.6);
    box-shadow: 0 0 35px rgba(255,0,161,0.25);
}

/* Input */
input, textarea, select {
    background-color: #FFFFFF !important;
    color: #1A1A1A !important;
    border: 1px solid #DDD !important;
    border-radius: 12px !important;
    padding: 0.6rem 0.8rem !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    transition: all 0.2s ease;
}
input:focus, textarea:focus {
    border-color: #FF00A1 !important;
    box-shadow: 0 0 10px rgba(255,0,161,0.25);
}

/* Buttons */
div.stButton > button:first-child {
    background: linear-gradient(90deg, #FF00A1, #7904EB);
    color: #FFFFFF;
    border-radius: 10px;
    border: none;
    font-weight: 600;
    padding: 0.6rem 1.3rem;
    transition: all 0.25s ease;
    box-shadow: 0 4px 14px rgba(121,4,235,0.25);
}
div.stButton > button:first-child:hover {
    background: linear-gradient(90deg, #FE76FF, #8A2BE2);
    transform: translateY(-2px);
    box-shadow: 0 0 20px rgba(255,0,161,0.4);
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 14px; }
.stTabs [data-baseweb="tab"] {
    height: 44px;
    padding: 0 20px;
    font-weight: 500;
    color: #555;
    background-color: #F0F0F9;
    border-radius: 10px 10px 0 0;
    transition: all 0.3s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    background: #F7E5FF;
    color: #000;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(90deg, #FF00A1, #7904EB);
    color: #FFFFFF !important;
    box-shadow: 0 0 12px rgba(255,0,161,0.3);
}

/* Alerts */
.stAlert > div {
    background-color: #FFF5FF;
    border-left: 4px solid #FF00A1;
    color: #333;
    border-radius: 10px;
}

/* Cards */
.metric-card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 1.2rem;
    border: 1px solid rgba(0,0,0,0.06);
    box-shadow: 0 5px 20px rgba(121,4,235,0.05);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.metric-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 25px rgba(121,4,235,0.15);
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid rgba(0,0,0,0.05);
}

/* Link */
a {
    color: #7904EB;
    text-decoration: none;
    font-weight: 500;
}
a:hover {
    color: #FF00A1;
    text-shadow: 0 0 6px rgba(255,0,161,0.3);
}
</style>
""", unsafe_allow_html=True)


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "email" not in st.session_state:
    st.session_state.email = ""
if "page" not in st.session_state:
    st.session_state.page = "login"

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
