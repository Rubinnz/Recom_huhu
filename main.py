import streamlit as st
from home import show_home

st.set_page_config(
    page_title="Video Game Recommender System",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
html, body, [class*="css"] {
    background-color: #F8F9FF;
    color: #1A1A1A;
    font-family: 'Poppins', 'Segoe UI', sans-serif;
}
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
</style>
""", unsafe_allow_html=True)

def main():
    if "page" not in st.session_state:
        st.session_state.page = "home"
    show_home()

if __name__ == "__main__":
    main()
