import mysql.connector
import pandas as pd

CFG = {
    "host": "b5fsacyipaetgcqkwacb-mysql.services.clever-cloud.com",
    "user": "uzffiaml7jzguazv",
    "password": "o9O1qqAb2XjXtYN0b4kc",
    "database": "b5fsacyipaetgcqkwacb",
    "port": 3306
}

# Kết nối DB
conn = mysql.connector.connect(**CFG)

# Đọc bằng cursor
cur = conn.cursor()
cur.execute("SELECT game_id, user_id, rating FROM game_ratings LIMIT 10;")
for row in cur.fetchall():
    print(row)

cur.close()
conn.close()
