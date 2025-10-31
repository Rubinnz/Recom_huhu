import os, re, hashlib, time
import streamlit as st
from utils.email_utils import gen_code, send_code

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

# ==== Config DB (trùng format login.py để đồng bộ) ====
DB_CFG = {
    "host": os.getenv("MYSQL_ADDON_HOST"),
    "port": int(os.getenv("MYSQL_ADDON_PORT", "3306")),
    "user": os.getenv("MYSQL_ADDON_USER"),
    "password": os.getenv("MYSQL_ADDON_PASSWORD"),
    "database": os.getenv("MYSQL_ADDON_DB"),
}

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@gmail\.com$", re.IGNORECASE)

# ==== Helpers ====
def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

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

def _get_user_email(username: str) -> str | None:
    """Lấy email theo username; trả về None nếu không có."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT email FROM users WHERE username=%s", (username,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row[0] if row else None

def _update_password(username: str, new_hash: str) -> bool:
    """Cập nhật password_hash theo username. Trả về True nếu thành công."""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET password_hash=%s WHERE username=%s",
            (new_hash, username)
        )
        conn.commit()
        ok = cur.rowcount > 0
        cur.close(); conn.close()
        return ok
    except Error as e:
        st.error(f"Lỗi DB khi cập nhật mật khẩu: {e}")
        return False

def _pw_strength_msg(pw: str) -> tuple[bool, str]:
    if len(pw) < 8: return False, "≥ 8 ký tự"
    if not re.search(r"[A-Z]", pw): return False, "thiếu chữ hoa"
    if not re.search(r"[a-z]", pw): return False, "thiếu chữ thường"
    if not re.search(r"[0-9]", pw): return False, "thiếu chữ số"
    if not re.search(r"[^A-Za-z0-9]", pw): return False, "thiếu ký tự đặc biệt"
    return True, "Mạnh"

# ==== UI ====
def show_forgot_password():
    st.markdown('<div class="main-header">🎮 Video Game Recommender System</div>', unsafe_allow_html=True)
    _ensure_users_table()

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("### 🔁 Quên mật khẩu")
        st.markdown("Mã xác minh sẽ được **gửi đến Gmail hiện tại** của tài khoản.")

        stage_key = "_fp_stage"
        payload_key = "_fp_payload"

        if stage_key not in st.session_state:
            st.session_state[stage_key] = "ask_user"

        # =======================
        # STAGE 1: NHẬP USERNAME
        # =======================
        if st.session_state[stage_key] == "ask_user":
            username = st.text_input("👤 Tên đăng nhập", key="fp_username")

            c1, c2 = st.columns(2)
            with c1:
                send_btn = st.button("📨 Gửi mã xác minh", type="primary", key="fp_send_btn")
            with c2:
                back_btn = st.button("⬅️ Quay lại đăng nhập", key="fp_back_btn")

            if send_btn:
                if not username:
                    st.error("Vui lòng nhập tên đăng nhập.")
                else:
                    try:
                        email = _get_user_email(username)
                    except Exception as e:
                        st.error(f"Lỗi DB: {e}")
                        email = None

                    if not email:
                        st.error("Không tìm thấy tài khoản hoặc chưa có email. Vui lòng liên hệ admin.")
                    elif not EMAIL_RE.match(email):
                        st.error("Email của tài khoản không phải Gmail hợp lệ. Vui lòng liên hệ admin.")
                    else:
                        try:
                            code = gen_code(6)
                            st.session_state[payload_key] = {
                                "username": username,
                                "email": email,
                                "code": code,
                                "exp": time.time() + 600,  # 10 phút
                            }
                            send_code(email, code, purpose="Xác minh quên mật khẩu")
                            st.success(f"Đã gửi mã xác minh tới {email}.")
                            st.session_state[stage_key] = "verify"
                            st.rerun()  # 🔑 BẮT BUỘC để UI nhảy sang form nhập mã
                        except Exception as e:
                            st.error(f"Gửi email thất bại: {e}")

            if back_btn:
                st.session_state.page = "login"
                st.rerun()

        # ==========================
        # STAGE 2: NHẬP MÃ + ĐỔI MẬT
        # ==========================
        elif st.session_state[stage_key] == "verify":
            payload = st.session_state.get(payload_key) or {}

            st.text_input("Tên đăng nhập", value=payload.get("username",""), disabled=True)

            # Ô nhập MÃ XÁC MINH + MẬT KHẨU MỚI
            code_input = st.text_input("🔢 Mã xác minh", max_chars=6, key="fp_code_input")
            new_pw = st.text_input("🔒 Mật khẩu mới", type="password", key="fp_new_pw")
            if new_pw:
                ok_strength, note = _pw_strength_msg(new_pw)
                st.caption(("✅ " if ok_strength else "⚠️ ") + note)
            new_pw2 = st.text_input("🔒 Xác nhận mật khẩu mới", type="password", key="fp_new_pw2")

            c1, c2, c3 = st.columns([1,1,1])
            with c1:
                confirm_btn = st.button("✅ Xác nhận đổi mật khẩu", type="primary", key="fp_confirm_btn")
            with c2:
                resend_btn = st.button("🔁 Gửi lại mã", key="fp_resend_btn")
            with c3:
                cancel_btn = st.button("Hủy & quay lại", key="fp_cancel_btn")

            # Gửi lại mã
            if resend_btn:
                if not payload.get("email") or not payload.get("username"):
                    st.error("Thiếu thông tin tài khoản. Hãy quay lại bước trước.")
                    st.session_state[stage_key] = "ask_user"
                    st.rerun()
                try:
                    code = gen_code(6)
                    st.session_state[payload_key] = {
                        "username": payload["username"],
                        "email": payload["email"],
                        "code": code,
                        "exp": time.time() + 600,
                    }
                    send_code(payload["email"], code, purpose="Xác minh quên mật khẩu (gửi lại)")
                    st.success(f"Đã gửi lại mã xác minh tới {payload['email']}.")
                except Exception as e:
                    st.error(f"Gửi email thất bại: {e}")

            # Xác nhận đổi mật khẩu
            if confirm_btn:
                if not code_input or not new_pw or not new_pw2:
                    st.error("Vui lòng nhập đầy đủ thông tin.")
                elif payload.get("exp", 0) < time.time():
                    st.error("Mã đã hết hạn. Vui lòng gửi lại mã mới.")
                elif code_input != payload.get("code"):
                    st.error("Mã xác minh không đúng.")
                else:
                    ok, note = _pw_strength_msg(new_pw)
                    if not ok:
                        st.error("Mật khẩu mới chưa đạt yêu cầu: " + note)
                    elif new_pw != new_pw2:
                        st.error("Xác nhận mật khẩu không khớp.")
                    else:
                        new_hash = _sha256(new_pw)
                        updated = _update_password(payload["username"], new_hash)
                        if updated:
                            st.success("✅ Đổi mật khẩu thành công! Mời đăng nhập lại.")
                            for k in ("_fp_stage","_fp_payload","fp_username","fp_code_input","fp_new_pw","fp_new_pw2"):
                                if k in st.session_state: del st.session_state[k]
                            st.session_state.page = "login"
                            st.rerun()
                        else:
                            st.error("Không thể cập nhật mật khẩu. Vui lòng thử lại hoặc liên hệ admin.")

            if cancel_btn:
                for k in ("_fp_stage","_fp_payload","fp_username","fp_code_input","fp_new_pw","fp_new_pw2"):
                    if k in st.session_state: del st.session_state[k]
                st.session_state.page = "login"
                st.rerun()
