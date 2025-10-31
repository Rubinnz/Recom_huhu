import os
import re
import hashlib
import streamlit as st
import mysql.connector
from mysql.connector import Error

from dotenv import load_dotenv

load_dotenv()

# ========= Helpers (giữ nguyên) =========
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def validate_username(username: str):
    username = (username or "").strip()
    if len(username) < 3:
        return False, "Tên đăng nhập phải có ít nhất 3 ký tự"
    if len(username) > 20:
        return False, "Tên đăng nhập không được quá 20 ký tự"
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "Tên đăng nhập chỉ được chứa chữ cái, số và dấu gạch dưới"
    return True, ""

def validate_password_basic(password: str):
    """Ràng buộc cơ bản để tránh nhập quá ngắn/dài (ngoài strength)."""
    if len(password) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự"
    if len(password) > 50:
        return False, "Mật khẩu không được quá 50 ký tự"
    return True, ""

def _pw_strength_msg(pw: str) -> tuple[bool, str]:
    if len(pw) < 8: return False, "≥ 8 ký tự"
    if not re.search(r"[A-Z]", pw): return False, "thiếu chữ hoa"
    if not re.search(r"[a-z]", pw): return False, "thiếu chữ thường"
    if not re.search(r"[0-9]", pw): return False, "thiếu chữ số"
    if not re.search(r"[^A-Za-z0-9]", pw): return False, "thiếu ký tự đặc biệt"
    return True, "Mạnh"

GMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@gmail\.com$", re.IGNORECASE)
def validate_gmail(email: str):
    email = (email or "").strip()
    if not GMAIL_RE.match(email):
        return False, "Gmail không hợp lệ (phải có đuôi @gmail.com)"
    return True, ""

# ========= DB Config =========
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
        raise RuntimeError(f"Thiếu cấu hình DB: {missing}. Hãy set biến môi trường Clever Cloud.")
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
    cur.close(); conn.close()

def username_exists(username: str) -> bool:
    """Kiểm tra username đã tồn tại trong DB."""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM users WHERE username=%s", (username,))
        ok = cur.fetchone() is not None
        cur.close(); conn.close()
        return ok
    except Error as e:
        st.error(f"Lỗi DB: {e}")
        return True  # chặn đăng ký khi DB lỗi

def email_exists(email: str) -> bool:
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM users WHERE email=%s", (email,))
        ok = cur.fetchone() is not None
        cur.close(); conn.close()
        return ok
    except Error as e:
        st.error(f"Lỗi DB: {e}")
        return True

def save_user(username: str, password: str, email: str) -> None:
    """Lưu user: username|sha256|email  ->  vào DB"""
    pw_hash = hash_password(password)
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s)",
        (username, pw_hash, email)
    )
    conn.commit()
    cur.close(); conn.close()

# ========= UI (giữ nguyên layout/flow) =========
def show_register():
    _ensure_users_table()

    st.markdown('<div class="main-header">🎮 Video Game Recommender System</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 📝 Đăng Ký Tài Khoản")
        st.markdown("---")

        with st.form("register_form"):
            username = st.text_input("👤 Tên đăng nhập", placeholder="Chọn tên đăng nhập (3-20 ký tự)")
            email = st.text_input("📧 Gmail", placeholder="yourname@gmail.com")

            password = st.text_input("🔒 Mật khẩu",
                                     type="password",
                                     placeholder="Ít nhất 8 ký tự, có hoa/thường/số/ký tự đặc biệt")
            # Hiển thị strength theo _pw_strength_msg
            if password:
                ok_strength, note = _pw_strength_msg(password)
                st.caption(("✅ " if ok_strength else "⚠️ ") + f"Độ mạnh mật khẩu: {note}")

            confirm_password = st.text_input("🔒 Xác nhận mật khẩu", type="password", placeholder="Nhập lại mật khẩu")

            c1, c2 = st.columns(2)
            with c1:
                submit_button = st.form_submit_button("Đăng ký", type="primary", use_container_width=True)
            with c2:
                back_button = st.form_submit_button("Quay lại", use_container_width=True)

            if submit_button:
                # Kiểm tra trống
                if not username or not email or not password or not confirm_password:
                    st.error("⚠️ Vui lòng nhập đầy đủ thông tin!")
                else:
                    # Username
                    ok, msg = validate_username(username)
                    if not ok:
                        st.error(f"❌ {msg}")
                    elif username_exists(username.strip()):
                        st.error("❌ Tên đăng nhập đã tồn tại!")
                    else:
                        # Gmail
                        ok, msg = validate_gmail(email)
                        if not ok:
                            st.error(f"❌ {msg}")
                        elif email_exists(email.strip()):
                            st.error("❌ Email đã được sử dụng!")
                        else:
                            # Kiểm tra cơ bản độ dài trước
                            ok, msg = validate_password_basic(password)
                            if not ok:
                                st.error(f"❌ {msg}")
                            else:
                                # Strength theo _pw_strength_msg (bắt buộc đạt chuẩn)
                                ok_strength, note = _pw_strength_msg(password)
                                if not ok_strength:
                                    st.error(f"❌ Mật khẩu chưa đạt yêu cầu: {note}")
                                elif password != confirm_password:
                                    st.error("❌ Mật khẩu xác nhận không khớp!")
                                else:
                                    try:
                                        save_user(username.strip(), password, email.strip())
                                        st.success(f"✅ Đăng ký thành công! Chào mừng {username.strip()}!")
                                        st.session_state.page = "login"
                                        st.rerun()
                                    except Error as e:
                                        st.error(f"Không thể lưu tài khoản: {e}")

            if back_button:
                st.session_state.page = "login"
                st.rerun()

        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; color: gray; font-size: 0.9em;'>"
            "Đã có tài khoản? Nhấn nút Quay lại để đăng nhập"
            "</div>",
            unsafe_allow_html=True
        )
