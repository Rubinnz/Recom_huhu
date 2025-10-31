import os
import streamlit as st
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import hashlib

load_dotenv()

DB_CFG = {
    "host": os.getenv("MYSQL_ADDON_HOST"),
    "port": int(os.getenv("MYSQL_ADDON_PORT", "3306")),
    "user": os.getenv("MYSQL_ADDON_USER"),
    "password": os.getenv("MYSQL_ADDON_PASSWORD"),
    "database": os.getenv("MYSQL_ADDON_DB"),
}

def _get_conn():
    return mysql.connector.connect(**DB_CFG)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def update_password(email, new_password):
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE users SET password_hash=%s WHERE email=%s",
                    (hash_password(new_password), email))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Error as e:
        st.error(f"Lỗi: {e}")
        return False

def show_forgot_password():
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
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-header">🔑 Quên mật khẩu</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h4 style='text-align:center;'>Khôi phục mật khẩu</h4>", unsafe_allow_html=True)
        with st.form("forgot_form"):
            email = st.text_input("📧 Nhập email của bạn", placeholder="example@gmail.com")
            new_pass = st.text_input("🔒 Mật khẩu mới", type="password", placeholder="Nhập mật khẩu mới")
            confirm = st.text_input("✅ Xác nhận mật khẩu mới", type="password", placeholder="Nhập lại mật khẩu")

            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            space1, c1, c2, space2 = st.columns([1, 2, 2, 1])
            with c1:
                reset_btn = st.form_submit_button("Đặt lại mật khẩu", type="primary", use_container_width=True)
            with c2:
                back_btn = st.form_submit_button("Quay lại", use_container_width=True)

            if reset_btn:
                if not email or not new_pass:
                    st.error("⚠️ Vui lòng nhập đủ thông tin!")
                elif new_pass != confirm:
                    st.error("❌ Mật khẩu xác nhận không trùng khớp!")
                else:
                    if update_password(email, new_pass):
                        st.success("✅ Cập nhật mật khẩu thành công!")
                        st.session_state.page = "login"
                        st.rerun()

            if back_btn:
                st.session_state.page = "login"
                st.rerun()
