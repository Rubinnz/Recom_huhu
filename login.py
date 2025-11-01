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
    missing = [k for k, v in DB_CFG.items() if not v]
    if missing:
        raise RuntimeError(f"Missing DB config: {missing}. Set Clever Cloud environment variables.")
    return mysql.connector.connect(**DB_CFG)

def _ensure_users_table():
    sql = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(64) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP NULL DEFAULT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()

def verify_credentials(username: str, password: str):
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT password_hash, email FROM users WHERE username=%s", (username,))
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return False, None
        stored_hash, email = row
        ok = (hash_password(password) == stored_hash)
        if ok:
            cur.execute("UPDATE users SET last_login = NOW() WHERE username=%s", (username,))
            conn.commit()
        cur.close()
        conn.close()
        return ok, (email if ok else None)
    except Error as e:
        st.error(f"Unable to connect to DB: {e}")
        return False, None

def show_login():
    st.markdown('<div class="main-header">🎮 Video Game Recommender System</div>', unsafe_allow_html=True)
    _ensure_users_table()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔐 Log In")
        st.markdown("---")
        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")

            space1, c1, c2, c3, space2 = st.columns([0.5, 1.5, 1.5, 1.5, 0.5])
            with c1:
                submit_button = st.form_submit_button("Log In", type="primary", use_container_width=True)
            with c2:
                register_button = st.form_submit_button("Register", use_container_width=True)
            with c3:
                forgot_button = st.form_submit_button("Forgot password?", use_container_width=True)

            if submit_button:
                if not username or not password:
                    st.error("⚠️ Please fill out all fields!")
                else:
                    ok, email = verify_credentials(username, password)
                    if ok:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.email = email or ""
                        st.session_state.page = "home"
                        st.success(f"✅ Login successful! Welcome, {username}!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password!")
            if register_button:
                st.session_state.page = "register"
                st.rerun()
            if forgot_button:
                st.session_state.page = "forgot"
                st.rerun()
        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; color: gray; font-size: 0.9em;'>"
            "Don't have an account? Click Register above."
            "</div>",
            unsafe_allow_html=True
        )
