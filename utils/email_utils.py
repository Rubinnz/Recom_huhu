import smtplib, ssl, random, string
from email.message import EmailMessage

# ====== Cấu hình SMTP trực tiếp ======
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "vuquockhanhdz@gmail.com"
SMTP_PASS = "zrtu hiry jrqr ifgz"  # app password của Gmail
SMTP_FROM = "vuquockhanhdz@gmail.com"

def gen_code(n: int = 6) -> str:
    """Sinh mã xác minh gồm số"""
    return "".join(random.choices(string.digits, k=n))

def send_code(to_email: str, code: str, purpose: str = "Xác minh"):
    """Gửi mã xác minh đến email"""
    msg = EmailMessage()
    msg["Subject"] = f"[Video Game Recommender] {purpose}"
    msg["From"] = SMTP_FROM
    msg["To"] = to_email
    msg.set_content(
        f"Xin chào,\n\nMã xác minh của bạn là: {code}\nMã sẽ hết hạn sau 10 phút.\n\n-- Video Game Recommender"
    )

    context = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls(context=context)
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
