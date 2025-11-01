import smtplib, ssl, random, string
from email.message import EmailMessage

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "vuquockhanhdz@gmail.com"
SMTP_PASS = "zrtu hiry jrqr ifgz"
SMTP_FROM = "vuquockhanhdz@gmail.com"

def gen_code(n: int = 6) -> str:
    """Generate a numeric verification code"""
    return "".join(random.choices(string.digits, k=n))

def send_code(to_email: str, code: str, purpose: str = "Verification"):
    """Send a verification code via email"""
    msg = EmailMessage()
    msg["Subject"] = f"[Video Game Recommender] {purpose}"
    msg["From"] = SMTP_FROM
    msg["To"] = to_email
    msg.set_content(
        f"Hello,\n\nYour verification code is: {code}\nThis code will expire in 10 minutes.\n\n-- Video Game Recommender"
    )

    context = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls(context=context)
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
