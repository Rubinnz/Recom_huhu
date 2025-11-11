import pandas as pd
import mysql.connector
from mysql.connector import Error

import os
from dotenv import load_dotenv

load_dotenv()  # Tự động đọc file .env trong thư mục hiện tại

DB_CFG = {
    "host": os.getenv("MYSQL_ADDON_HOST"),
    "port": int(os.getenv("MYSQL_ADDON_PORT", 3306)),
    "user": os.getenv("MYSQL_ADDON_USER"),
    "password": os.getenv("MYSQL_ADDON_PASSWORD"),
    "database": os.getenv("MYSQL_ADDON_DB"),
}


TABLE = "game_ratings"
CSV_PATH = "game_ratings.csv"

def to_int_or_none(x):
    try:
        return int(float(x))
    except Exception:
        return None

def to_str_or_none(x):
    if pd.isna(x):
        return None
    s = str(x).strip()
    return s if s else None

def main():
    conn = mysql.connector.connect(**CFG)
    cur = conn.cursor()

    cur.execute(f"DROP TABLE IF EXISTS {TABLE}")

    cur.execute(f"""
        CREATE TABLE {TABLE} (
            game_id INT NOT NULL,
            user_id VARCHAR(64) NOT NULL,
            rating  INT NULL,
            PRIMARY KEY (game_id, user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    conn.commit()

    df = pd.read_csv(CSV_PATH)
    df.columns = [c.strip().lower() for c in df.columns]

    df["game_id"] = df["game_id"].map(to_int_or_none)
    df["user_id"] = df["user_id"].map(to_str_or_none)
    df["rating"]  = df["rating"].map(to_int_or_none)

    before = len(df)
    df = df.dropna(subset=["game_id","user_id"])
    print(f"Giữ {len(df)}/{before} dòng sau khi làm sạch.")

    rows = list(df[["game_id","user_id","rating"]].itertuples(index=False, name=None))
    if rows:
        sql = f"INSERT INTO {TABLE} (game_id, user_id, rating) VALUES (%s, %s, %s)"
        cur.executemany(sql, rows)
        conn.commit()
        print(f"Import thành công {len(rows)} dòng.")
    else:
        print("Không có dữ liệu hợp lệ để import.")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
