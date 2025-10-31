# data.py — unified loader: MySQL first, CSV fallback
import os
from typing import Tuple, List, Optional
import pandas as pd

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

# Có đủ thông tin thì mới dùng DB
USE_DB = all(DB_CFG.values())

# ======= CSV fallback paths (giữ logic cũ) =======
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

CANDIDATE_GAMES: List[str] = [
    os.path.join(BASE_DIR, "game_metadata.csv"),
    os.path.join(DATA_DIR, "game_metadata.csv"),
]
CANDIDATE_RATINGS: List[str] = [
    os.path.join(BASE_DIR, "game_ratings.csv"),
    os.path.join(DATA_DIR, "game_ratings.csv"),
]

def _first_existing(paths: List[str]) -> Optional[str]:
    for p in paths:
        if os.path.exists(p):
            return p
    return None

GAMES_PATH = _first_existing(CANDIDATE_GAMES)
RATINGS_PATH = _first_existing(CANDIDATE_RATINGS)

# ======= Helpers chung =======
def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    return df

def _ensure_cols(df: pd.DataFrame, cols: List[str], fill="") -> pd.DataFrame:
    for c in cols:
        if c not in df.columns:
            df[c] = fill
    return df

# ======= Load từ MySQL =======
def _connect_mysql():
    """Tạo kết nối MySQL bằng mysql-connector (để pandas.read_sql sử dụng)."""
    import mysql.connector  # lazy import
    return mysql.connector.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database=DB_NAME
    )

def _load_games_from_db(limit: Optional[int] = None) -> pd.DataFrame:
    """
    Đọc bảng game_metadata (đã tạo bởi import_metadata.py) từ MySQL.
    Cột chuẩn hoá trả về: id, title, genres, platforms (+ rating, released, cover_image, game_link nếu cần).
    """
    # Lưu ý: import_metadata.py tạo bảng 'game_metadata' với schema: game_id, name, description, genres, platforms, rating, released, cover_image, game_link
    # (xem script import của bạn). :contentReference[oaicite:1]{index=1}
    base_sql = """
        SELECT 
            game_id AS id,
            name    AS title,
            genres,
            platforms,
            rating,
            released,
            cover_image,
            game_link
        FROM game_metadata
    """
    if limit and limit > 0:
        base_sql += f" LIMIT {int(limit)}"

    try:
        conn = _connect_mysql()
        df = pd.read_sql(base_sql, conn)
        conn.close()
    except Exception:
        # Nếu lỗi DB → fallback CSV
        return _load_games_from_csv(limit)

    df = _normalize_columns(df)
    df = _ensure_cols(df, ["id", "title", "genres", "platforms"])
    # ép kiểu nhẹ
    df["id"] = df["id"].astype(str)
    for c in ["title", "genres", "platforms"]:
        df[c] = df[c].astype(str).fillna("")
    return df

def _load_ratings_from_db(limit: Optional[int] = None) -> pd.DataFrame:
    """
    Đọc bảng game_ratings (đã tạo bởi import_ratings.py) từ MySQL.
    Cột chuẩn hoá trả về: userid, itemid, rating.
    """
    # Lưu ý: import_ratings.py tạo bảng 'game_ratings' với schema: game_id (INT), user_id (VARCHAR), rating (INT), PK(game_id, user_id). :contentReference[oaicite:2]{index=2}
    base_sql = """
        SELECT 
            user_id AS userid,
            game_id AS itemid,
            rating
        FROM game_ratings
    """
    if limit and limit > 0:
        base_sql += f" LIMIT {int(limit)}"

    try:
        conn = _connect_mysql()
        df = pd.read_sql(base_sql, conn)
        conn.close()
    except Exception:
        # Nếu lỗi DB → fallback CSV
        return _load_ratings_from_csv(limit)

    df = _normalize_columns(df)
    df = _ensure_cols(df, ["userid", "itemid", "rating"], fill=None)

    df["userid"] = df["userid"].astype(str)
    df["itemid"] = df["itemid"].astype(str)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df = df.dropna(subset=["userid", "itemid", "rating"])
    return df

# ======= Load từ CSV (fallback) — dựa theo file gốc của bạn =======
def _load_games_from_csv(nrows: Optional[int] = None) -> pd.DataFrame:
    if not GAMES_PATH:
        return pd.DataFrame()
    try:
        df = pd.read_csv(GAMES_PATH, nrows=nrows, low_memory=False, encoding_errors="ignore")
    except Exception:
        return pd.DataFrame()

    df = _normalize_columns(df)

    # Map id
    if "id" not in df.columns:
        for c in ("game_id", "itemid", "item_id"):
            if c in df.columns:
                df = df.rename(columns={c: "id"})
                break
    # Map title
    if "title" not in df.columns:
        for c in ("name", "game", "item_name", "title_name"):
            if c in df.columns:
                df = df.rename(columns={c: "title"})
                break

    df = _ensure_cols(df, ["id", "title", "genres", "platforms"])
    df["id"] = df["id"].astype(str)
    df["title"] = df["title"].astype(str).fillna("")
    df["genres"] = df["genres"].astype(str).fillna("")
    df["platforms"] = df["platforms"].astype(str).fillna("")
    return df

def _load_ratings_from_csv(nrows: Optional[int] = None) -> pd.DataFrame:
    if not RATINGS_PATH:
        return pd.DataFrame()
    try:
        df = pd.read_csv(RATINGS_PATH, nrows=nrows, low_memory=False, encoding_errors="ignore")
    except Exception:
        return pd.DataFrame()

    df = _normalize_columns(df)

    # userid
    if "userid" not in df.columns:
        for c in ("user_id", "user", "u"):
            if c in df.columns:
                df = df.rename(columns={c: "userid"})
                break
    # itemid
    if "itemid" not in df.columns:
        for c in ("item_id", "game_id", "id", "item"):
            if c in df.columns:
                df = df.rename(columns={c: "itemid"})
                break
    # rating
    if "rating" not in df.columns:
        for c in ("score", "stars", "rate", "ratings"):
            if c in df.columns:
                df = df.rename(columns={c: "rating"})
                break

    df = _ensure_cols(df, ["userid", "itemid", "rating"], fill=None)
    df["userid"] = df["userid"].astype(str)
    df["itemid"] = df["itemid"].astype(str)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")

    # timestamp optional
    for tcol in ("timestamp", "time", "ts", "created_at"):
        if tcol in df.columns:
            df = df.rename(columns={tcol: "timestamp"})
            break

    df = df.dropna(subset=["userid", "itemid", "rating"])
    return df

# ======= Public API =======
def load_games(nrows: Optional[int] = None) -> pd.DataFrame:
    """Đọc metadata game. Ưu tiên DB; fallback CSV."""
    if USE_DB:
        return _load_games_from_db(limit=nrows)
    return _load_games_from_csv(nrows=nrows)

def load_ratings(nrows: Optional[int] = None) -> pd.DataFrame:
    """Đọc ratings. Ưu tiên DB; fallback CSV."""
    if USE_DB:
        return _load_ratings_from_db(limit=nrows)
    return _load_ratings_from_csv(nrows=nrows)

def get_dataset(nrows_games: Optional[int] = None, nrows_ratings: Optional[int] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Trả về (games, ratings) đã chuẩn hoá cột."""
    return load_games(nrows_games), load_ratings(nrows_ratings)
