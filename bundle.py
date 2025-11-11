# build_hybrid_bundle.py
import os
import sys
import pandas as pd
import numpy as np
import joblib
from dotenv import load_dotenv

# pip install mysql-connector-python
import mysql.connector
from mysql.connector import Error

# Import the functional hybrid builder
from utils.recommender_utils import build_and_save_hybrid

# ------------------ CONFIG (edit as needed) ------------------
CF_MODEL_DIR    = "./model/best_cf_model_SVD.pkl"   # folder chứa các file best_cf_model_*.pkl
CB_MODEL_PATH   = "./model/best_cb_model_CB_Genres_Description.pkl"
CF_SUMMARY_CSV  = "cf_summary.csv"  # file có cột: Model, Combined_Score
OUT_BUNDLE_PATH = "./model/hybrid_bundle.pkl"

RATINGS_TABLE = "game_ratings"  # (game_id INT, user_id VARCHAR, rating INT)
GAMES_TABLE   = "games"         # (game_id INT PRIMARY KEY, name TEXT, ...)

# Fallback CSVs nếu chưa có table games
GAMES_CSV_FALLBACK = "games.csv"   # cần cột: game_id, name

# ------------------------------------------------------------

def get_db_cfg_from_env():
    load_dotenv()
    cfg = {
        "host": os.getenv("MYSQL_ADDON_HOST"),
        "port": int(os.getenv("MYSQL_ADDON_PORT", "3306")),
        "user": os.getenv("MYSQL_ADDON_USER"),
        "password": os.getenv("MYSQL_ADDON_PASSWORD"),
        "database": os.getenv("MYSQL_ADDON_DB"),
    }
    missing = [k for k, v in cfg.items() if v in (None, "")]
    if missing:
        raise RuntimeError(f"Thiếu biến môi trường cho MySQL: {missing}")
    return cfg

def fetch_ratings_df(conn, table):
    q = f"SELECT game_id, user_id, rating FROM {table}"
    df = pd.read_sql(q, con=conn)
    # làm sạch tối thiểu
    df = df.dropna(subset=["game_id","user_id"])
    # ép kiểu an toàn
    df["game_id"] = df["game_id"].astype(str)
    df["user_id"] = df["user_id"].astype(str)
    if "rating" in df.columns:
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    return df

def fetch_games_df(conn, table, fallback_csv=None):
    try:
        q = f"SELECT game_id, name FROM {table}"
        df = pd.read_sql(q, con=conn)
        if df.empty:
            raise ValueError("Bảng games rỗng.")
        # ép kiểu tối thiểu
        df["game_id"] = df["game_id"].astype(str)
        df["name"] = df["name"].astype(str)
        return df
    except Exception as e:
        if fallback_csv and Path(fallback_csv).exists():
            print(f"[WARN] Không thể đọc bảng {table} ({e}). Dùng fallback CSV: {fallback_csv}")
            df = pd.read_csv(fallback_csv)
            need = {"game_id","name"}
            if not need.issubset(df.columns):
                raise RuntimeError(f"CSV fallback thiếu cột {need}")
            df["game_id"] = df["game_id"].astype(str)
            df["name"] = df["name"].astype(str)
            return df
        raise

def load_cf_summary(path):
    if not Path(path).exists():
        raise FileNotFoundError(f"Không thấy file CF summary: {path}")
    df = pd.read_csv(path)
    need = {"Model","Combined_Score"}
    if not need.issubset(df.columns):
        raise RuntimeError(f"cf_summary.csv thiếu cột {need}")
    # đảm bảo Combined_Score là số
    df["Combined_Score"] = pd.to_numeric(df["Combined_Score"], errors="coerce")
    if df["Combined_Score"].isna().all():
        raise RuntimeError("Combined_Score toàn NaN.")
    return df

def main():
    print("==> Kết nối MySQL...")
    cfg = get_db_cfg_from_env()
    conn = mysql.connector.connect(**cfg)

    print("==> Đọc ratings...")
    train_df = fetch_ratings_df(conn, RATINGS_TABLE)
    if train_df.empty:
        raise RuntimeError("Không có dữ liệu ratings trong bảng.")

    print("==> Đọc games...")
    games_df = fetch_games_df(conn, GAMES_TABLE, fallback_csv=GAMES_CSV_FALLBACK)
    if games_df.empty:
        raise RuntimeError("Không có dữ liệu games.")

    print("==> Đọc CF summary...")
    cf_df = load_cf_summary(CF_SUMMARY_CSV)

    print("==> Xây bundle hybrid (no-class)...")
    out_path = build_and_save_hybrid(
        cf_df=cf_df,
        train_df=train_df.rename(columns={"game_id":"game_id","user_id":"user_id","rating":"rating"}),
        games_df=games_df.rename(columns={"game_id":"game_id","name":"name"}),
        cf_model_dir=CF_MODEL_DIR,
        cb_model_path=CB_MODEL_PATH,
        out_path=OUT_BUNDLE_PATH,
        cf_weight=0.7,
        random_state=42,
    )

    print(f"✅ Đã lưu bundle: {out_path}")
    conn.close()

if __name__ == "__main__":
    main()
