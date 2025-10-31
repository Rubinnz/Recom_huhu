import os, mysql.connector
cfg = {
    "host": os.getenv("MYSQL_ADDON_HOST"),
    "port": int(os.getenv("MYSQL_ADDON_PORT", "3306")),
    "user": os.getenv("MYSQL_ADDON_USER"),
    "password": os.getenv("MYSQL_ADDON_PASSWORD"),
    # KHÔNG thêm "database" ở test 1
}
conn = mysql.connector.connect(**cfg)
cur = conn.cursor()
cur.execute("SELECT CURRENT_USER(), VERSION()")
print("✅ Auth OK as:", cur.fetchone())
cur.close(); conn.close()
