import os
import streamlit as st
import hashlib
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

DB_CFG = {
    "host": os.getenv("MYSQL_ADDON_HOST"),
    "port": int(os.getenv("MYSQL_ADDON_PORT", "3306")),
    "user": os.getenv("MYSQL_ADDON_USER"),
    "password": os.getenv("MYSQL_ADDON_PASSWORD"),
    "database": os.getenv("MYSQL_ADDON_DB"),
}

def _get_conn():
    return mysql.connector.connect(**DB_CFG)

def create_user(username: str, password: str, email: str):
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s)",
                    (username, hash_password(password), email))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Error as e:
        st.error(f"Lỗi: {e}")
        return False

def show_register():
    st.markdown("""
    <style>
    body, [class*="css"] {background-color: #0E0B1F; color: #FFFFFF; font-family: 'Segoe UI', sans-serif;}
    .main-header {
        font-size: 2.3rem; font-weight: 700; text-align: center;
        background: linear-gradient(90deg, #8A2BE2, #FF6EC7);
        border-radius: 12px; padding: 1rem; margin-bottom: 1.5rem;
        box-shadow: 0 0 25px rgba(255,110,199,0.4);
    }
    input[type=text], input[type=password], input[type=email] {
        background-color: #FFFFFF !important; color: #000000 !important;
        border-radius: 8px !important; border: 1px solid #4ADEDE !important;
        padding: 8px !important;
    }
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #8A2BE2, #FF6EC7);
        color: #FFFFFF; border-radius: 8px; border: none; font-weight: 600;
        transition: all 0.3s ease; height: 40px;
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(90deg, #FF6EC7, #8A2BE2);
        box-shadow: 0 0 15px rgba(255,110,199,0.5); transform: translateY(-1px);
    }
    hr {border: none; border-top: 1px solid rgba(255,255,255,0.1); margin: 10px 0 20px 0;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-header">📝 Tạo tài khoản mới</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h4 style='text-align:center;'>Đăng Ký</h4>", unsafe_allow_html=True)
        with st.form("register_form"):
            username = st.text_input("👤 Tên đăng nhập", placeholder="Tối thiểu 3 ký tự")
            email = st.text_input("📧 Email", placeholder="example@gmail.com")
            password = st.text_input("🔒 Mật khẩu", type="password", placeholder="Nhập mật khẩu")
            confirm = st.text_input("✅ Xác nhận mật khẩu", type="password", placeholder="Nhập lại mật khẩu")

            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            space1, c1, c2, space2 = st.columns([1, 2, 2, 1])
            with c1:
                register_button = st.form_submit_button("Tạo tài khoản", type="primary", use_container_width=True)
            with c2:
                back_button = st.form_submit_button("Quay lại", use_container_width=True)

            if register_button:
                if not username or not password or not email:
                    st.error("⚠️ Điền đầy đủ thông tin!")
                elif password != confirm:
                    st.error("❌ Mật khẩu xác nhận không trùng khớp!")
                else:
                    if create_user(username, password, email):
                        st.success("✅ Tạo tài khoản thành công! Hãy đăng nhập.")
                        st.session_state.page = "login"
                        st.rerun()

            if back_button:
                st.session_state.page = "login"
                st.rerun()
