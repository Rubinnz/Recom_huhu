import os, mysql.connector
cfg = {
    "host": os.getenv("MYSQL_ADDON_HOST"),
    "port": int(os.getenv("MYSQL_ADDON_PORT", "3306")),
    "user": os.getenv("MYSQL_ADDON_USER"),
    "password": os.getenv("MYSQL_ADDON_PASSWORD"),
    "database": os.getenv("MYSQL_ADDON_DB"),
}
conn = mysql.connector.connect(**cfg)
cur = conn.cursor()
cur.execute("SHOW TABLES")
print("Tables:", cur.fetchall())
cur.close(); conn.close()
print("✅ DB OK")
