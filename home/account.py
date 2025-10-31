import os, re, hashlib, time
import streamlit as st
import mysql.connector
from mysql.connector import Error
from utils.email_utils import gen_code, send_code
from dotenv import load_dotenv

load_dotenv()

# ================== DB Config ==================
DB_CFG = {
    "host": os.getenv("MYSQL_ADDON_HOST"),
    "port": int(os.getenv("MYSQL_ADDON_PORT", "3306")),
    "user": os.getenv("MYSQL_ADDON_USER"),
    "password": os.getenv("MYSQL_ADDON_PASSWORD"),
    "database": os.getenv("MYSQL_ADDON_DB"),
}

def _get_conn():
    return mysql.connector.connect(**DB_CFG)

# ================== Helpers ==================
# Cho phép mọi định dạng email miễn có @
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", re.IGNORECASE)

def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _check_pw(stored_pw: str, given_pw: str) -> bool:
    return (_sha256(given_pw) == stored_pw)

def _pw_strength_msg(pw: str) -> tuple[bool, str]:
    if len(pw) < 8: return False, "≥ 8 ký tự"
    if not re.search(r"[A-Z]", pw): return False, "thiếu chữ hoa"
    if not re.search(r"[a-z]", pw): return False, "thiếu chữ thường"
    if not re.search(r"[0-9]", pw): return False, "thiếu chữ số"
    if not re.search(r"[^A-Za-z0-9]", pw): return False, "thiếu ký tự đặc biệt"
    return True, "Mạnh"

# ================== DB Actions ==================
def _get_user(username: str):
    conn = _get_conn(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT username, password_hash, email FROM users WHERE username=%s", (username,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row

def _update_password(username: str, new_pw: str):
    pw_hash = _sha256(new_pw)
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("UPDATE users SET password_hash=%s WHERE username=%s", (pw_hash, username))
    conn.commit(); cur.close(); conn.close()

def _update_email(username: str, new_email: str):
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("UPDATE users SET email=%s WHERE username=%s", (new_email, username))
    conn.commit(); cur.close(); conn.close()

# ================== Reset flows ==================
def _reset_pwd_flow():
    for k in (
        "_pwd_verify", "pwd_verify_code", "_pwd_code_verified",
        "acc_old_pw", "acc_new_pw", "acc_cfm_pw"
    ):
        if k in st.session_state: del st.session_state[k]

def _reset_email_flow():
    for k in ("_email_change_verify", "acc_email_code", "_email_code_verified", "acc_new_email"):
        if k in st.session_state: del st.session_state[k]

# ================== UI ==================
def render_account_tab(username: str):
    st.subheader("⚙️ Cài đặt tài khoản")

    me = _get_user(username)
    if not me:
        st.error("Không tìm thấy tài khoản.")
        return

    current_email = me["email"] or st.session_state.get("email", "")

    st.text_input("Tên đăng nhập", value=username, disabled=True)
    st.text_input("Email hiện tại", value=current_email, disabled=True)

    st.markdown("")
    bcol1, bcol2 = st.columns(2)
    with bcol1:
        if st.button("🔑 Đổi mật khẩu", key="btn_show_change_pwd", use_container_width=True):
            st.session_state.show_change_pass = True
            st.session_state.show_change_email = False
    with bcol2:
        if st.button("📧 Đổi Email", key="btn_show_change_email", use_container_width=True):
            st.session_state.show_change_email = True
            st.session_state.show_change_pass = False

    st.markdown("---")

    # ================== FLOW: ĐỔI MẬT KHẨU ==================
    if st.session_state.get("show_change_pass"):
        st.markdown("#### 🔑 Đổi mật khẩu (mã gửi tới Email hiện tại)")

        if not current_email or not EMAIL_RE.match(current_email):
            st.warning("Tài khoản chưa có Email hợp lệ. Hãy cập nhật Email trước.")
            return

        # Bước 1: gửi mã
        csend, ccode = st.columns([1, 1])
        with csend:
            if st.button("📨 Gửi mã xác minh", key="pwd_send_code", help="Gửi đến Email hiện tại", use_container_width=True):
                try:
                    code = gen_code(6)
                    st.session_state["_pwd_verify"] = {
                        "username": username,
                        "email": current_email,
                        "code": code,
                        "exp": time.time() + 600,
                    }
                    st.session_state._pwd_code_verified = False
                    send_code(current_email, code, "Xác minh đổi mật khẩu")
                    st.success(f"Đã gửi mã xác minh tới {current_email}.")
                except Exception as e:
                    st.error(f"Gửi email thất bại: {e}")

        with ccode:
            code_input = st.text_input("Nhập mã xác minh", max_chars=6, key="pwd_verify_code")
            if st.button("✅ Xác nhận mã", key="pwd_confirm_code", use_container_width=True):
                payload = st.session_state.get("_pwd_verify")
                if not payload:
                    st.error("Bạn chưa gửi mã xác minh.")
                elif payload["exp"] < time.time():
                    st.error("Mã đã hết hạn. Hãy gửi lại.")
                elif code_input != payload["code"]:
                    st.error("Mã xác minh không đúng.")
                else:
                    st.session_state._pwd_code_verified = True
                    st.success("Đã xác minh mã. Bạn có thể nhập mật khẩu mới.")

        # Bước 2: nhập mật khẩu mới
        disabled = not st.session_state.get("_pwd_code_verified", False)
        c1, c2, c3 = st.columns(3)
        with c1:
            old_pw = st.text_input("Mật khẩu hiện tại", type="password", key="acc_old_pw", disabled=disabled)
        with c2:
            new_pw = st.text_input("Mật khẩu mới", type="password", key="acc_new_pw", disabled=disabled)
            if new_pw and not disabled:
                ok_strength, note = _pw_strength_msg(new_pw)
                st.caption(("✅ " if ok_strength else "⚠️ ") + note)
        with c3:
            confirm_pw = st.text_input("Xác nhận mật khẩu", type="password", key="acc_cfm_pw", disabled=disabled)

        if st.button("🔄 Đổi mật khẩu", type="primary", key="confirm_change_pwd", use_container_width=True, disabled=disabled):
            payload = st.session_state.get("_pwd_verify")
            if not payload or not st.session_state.get("_pwd_code_verified"):
                st.error("Bạn cần xác nhận mã trước khi đổi mật khẩu.")
                return

            if not (old_pw and new_pw and confirm_pw):
                st.error("Hãy nhập đầy đủ mật khẩu.")
                return
            ok, note = _pw_strength_msg(new_pw)
            if not ok:
                st.error("Mật khẩu mới chưa đủ mạnh: " + note)
                return
            if new_pw != confirm_pw:
                st.error("Xác nhận mật khẩu không khớp.")
                return
            if not _check_pw(me["password_hash"], old_pw):
                st.error("Sai mật khẩu hiện tại.")
                return

            _update_password(username, new_pw)
            _reset_pwd_flow()
            st.success("Đổi mật khẩu thành công!")
            st.session_state.show_change_pass = False

    # ================== FLOW: ĐỔI EMAIL ==================
    if st.session_state.get("show_change_email"):
        st.markdown("#### 📧 Đổi Email (mã gửi tới Email hiện tại)")

        if not current_email or not EMAIL_RE.match(current_email):
            st.warning("Tài khoản chưa có Email hợp lệ.")
            return

        esend, ecode = st.columns([1, 1])
        with esend:
            if st.button("📨 Gửi mã xác minh", key="email_send_code", help="Gửi tới Email hiện tại", use_container_width=True):
                try:
                    code = gen_code(6)
                    st.session_state["_email_change_verify"] = {
                        "username": username,
                        "email": current_email,
                        "code": code,
                        "exp": time.time() + 600,
                    }
                    st.session_state._email_code_verified = False
                    send_code(current_email, code, "Xác minh đổi Email")
                    st.success(f"Đã gửi mã xác minh tới {current_email}.")
                except Exception as e:
                    st.error(f"Gửi email thất bại: {e}")

        with ecode:
            verify_code_email = st.text_input("Nhập mã xác minh", max_chars=6, key="acc_email_code")
            if st.button("✅ Xác nhận mã", key="email_confirm_code", use_container_width=True):
                payload = st.session_state.get("_email_change_verify")
                if not payload:
                    st.error("Bạn chưa gửi mã xác minh.")
                elif payload["exp"] < time.time():
                    st.error("Mã đã hết hạn. Hãy gửi lại.")
                elif verify_code_email != payload["code"]:
                    st.error("Mã xác minh không đúng.")
                else:
                    st.session_state._email_code_verified = True
                    st.success("Đã xác minh mã. Bạn có thể nhập Email mới.")

        disabled_email = not st.session_state.get("_email_code_verified", False)
        new_email = st.text_input("Email mới", placeholder="yourname@example.com", key="acc_new_email", disabled=disabled_email)

        if st.button("✅ Xác nhận & đổi Email", type="primary", key="confirm_change_email", use_container_width=True, disabled=disabled_email):
            if not new_email or not EMAIL_RE.match(new_email):
                st.error("Email mới không hợp lệ.")
                return
            if new_email == current_email:
                st.error("Email mới phải khác Email hiện tại.")
                return

            _update_email(username, new_email)
            st.session_state.email = new_email
            _reset_email_flow()
            st.success("Đổi Email thành công!")
            st.session_state.show_change_email = False
