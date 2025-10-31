import os, re, hashlib, time
import streamlit as st
from utils.email_utils import gen_code, send_code 

USER_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "users.txt"))
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@gmail\.com$", re.IGNORECASE)

# ==== Helpers ====
def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _parse_line(line: str):
    raw = line.rstrip("\n")
    if "|" in raw:
        parts = raw.split("|")
        if len(parts) == 3: return parts[0], parts[1], parts[2], "|"
        if len(parts) == 2: return parts[0], parts[1], "", "|"
    if ":" in raw:
        u, p = raw.split(":", 1)
        return u, p, "", ":"
    return None, None, None, None

def _load_users():
    rows = []
    if not os.path.exists(USER_FILE): return rows
    with open(USER_FILE, "r", encoding="utf-8") as f:
        for ln in f:
            u, p, e, sep = _parse_line(ln)
            if u: rows.append({"u": u, "p": p, "e": e or "", "sep": sep})
    return rows

def _save_users(rows):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        for r in rows:
            if r["sep"] == "|" and r.get("e"):
                f.write(f"{r['u']}|{r['p']}|{r['e']}\n")
            elif r["sep"] == "|":
                f.write(f"{r['u']}|{r['p']}\n")
            else:
                f.write(f"{r['u']}:{r['p']}\n")

def _pw_strength_msg(pw: str) -> tuple[bool, str]:
    if len(pw) < 8: return False, "≥ 8 ký tự"
    if not re.search(r"[A-Z]", pw): return False, "thiếu chữ hoa"
    if not re.search(r"[a-z]", pw): return False, "thiếu chữ thường"
    if not re.search(r"[0-9]", pw): return False, "thiếu chữ số"
    if not re.search(r"[^A-Za-z0-9]", pw): return False, "thiếu ký tự đặc biệt"
    return True, "Mạnh"

def show_forgot_password():
    st.markdown('<div class="main-header">🎮 Video Game Recommender System</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])

    with col2:
        st.markdown("### 🔁 Quên mật khẩu")
        st.markdown("Mã xác minh sẽ được **gửi đến Gmail hiện tại** của tài khoản.")

        if "_fp_stage" not in st.session_state:
            st.session_state._fp_stage = "ask_user"

        if st.session_state._fp_stage == "ask_user":
            username = st.text_input("👤 Tên đăng nhập", key="fp_username")
            c1, c2 = st.columns(2)
            with c1:
                send_btn = st.button("📨 Gửi mã xác minh", type="primary", key="fp_send", use_container_width=False, width="stretch")
            with c2:
                back_btn = st.button("⬅️ Quay lại đăng nhập", key="fp_back", width="stretch")

            if send_btn:
                if not username:
                    st.error("Vui lòng nhập tên đăng nhập.")
                else:
                    users = _load_users()
                    me = next((r for r in users if r["u"] == username), None)
                    if not me:
                        st.error("Không tìm thấy tài khoản.")
                    elif not me["e"] or not EMAIL_RE.match(me["e"]):
                        st.error("Tài khoản này chưa có Gmail hợp lệ. Vui lòng liên hệ admin.")
                    else:
                        try:
                            code = gen_code(6)
                            st.session_state._fp_payload = {
                                "username": username,
                                "email": me["e"],
                                "code": code,
                                "exp": time.time() + 600, 
                            }
                            send_code(me["e"], code, purpose="Xác minh quên mật khẩu")
                            st.session_state._fp_stage = "verify"
                            st.success(f"Đã gửi mã xác minh tới {me['e']}.")
                        except Exception as e:
                            st.error(f"Gửi email thất bại: {e}")

            if back_btn:
                st.session_state.page = "login"
                st.rerun()

        elif st.session_state._fp_stage == "verify":
            payload = st.session_state.get("_fp_payload")
            st.text_input("Tên đăng nhập", value=payload["username"], disabled=True)

            code_input = st.text_input("🔢 Mã xác minh", max_chars=6, key="fp_code_input")
            new_pw = st.text_input("🔒 Mật khẩu mới", type="password", key="fp_new_pw")
            if new_pw:
                ok_strength, note = _pw_strength_msg(new_pw)
                st.caption(("✅ " if ok_strength else "⚠️ ") + note)
            new_pw2 = st.text_input("🔒 Xác nhận mật khẩu mới", type="password", key="fp_new_pw2")

            c1, c2 = st.columns(2)
            with c1:
                confirm_btn = st.button("✅ Xác nhận đổi mật khẩu", type="primary", key="fp_confirm", width="stretch")
            with c2:
                cancel_btn = st.button("Hủy & quay lại", key="fp_cancel", width="stretch")

            if confirm_btn:
                if not code_input or not new_pw or not new_pw2:
                    st.error("Vui lòng nhập đầy đủ thông tin.")
                elif payload["exp"] < time.time():
                    st.error("Mã đã hết hạn. Vui lòng gửi lại mã mới.")
                    st.session_state._fp_stage = "ask_user"
                elif code_input != payload["code"]:
                    st.error("Mã xác minh không đúng.")
                else:
                    ok, note = _pw_strength_msg(new_pw)
                    if not ok:
                        st.error("Mật khẩu mới chưa đạt yêu cầu: " + note)
                    elif new_pw != new_pw2:
                        st.error("Xác nhận mật khẩu không khớp.")
                    else:
                        users = _load_users()
                        for r in users:
                            if r["u"] == payload["username"]:
                                r["p"] = _sha256(new_pw)  
                                r["sep"] = "|"            
                                if not r.get("e"):
                                    r["e"] = payload["email"]
                                _save_users(users)
                                st.success("✅ Đổi mật khẩu thành công! Mời đăng nhập lại.")
                                for k in ("_fp_stage","_fp_payload","fp_username","fp_code_input","fp_new_pw","fp_new_pw2"):
                                    if k in st.session_state: del st.session_state[k]
                                st.session_state.page = "login"
                                st.rerun()
                        else:
                            st.error("Không tìm thấy tài khoản. Hãy quay lại bước trước.")

            if cancel_btn:
                for k in ("_fp_stage","_fp_payload","fp_username","fp_code_input","fp_new_pw","fp_new_pw2"):
                    if k in st.session_state: del st.session_state[k]
                st.session_state.page = "login"
                st.rerun()
