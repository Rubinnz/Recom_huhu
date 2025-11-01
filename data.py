# data.py — simplified: only load game metadata (no ratings)
import os
from typing import Optional
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DB_CFG = {
    "host": os.getenv("MYSQL_ADDON_HOST"),
    "port": int(os.getenv("MYSQL_ADDON_PORT", 3306)),
    "user": os.getenv("MYSQL_ADDON_USER"),
    "password": os.getenv("MYSQL_ADDON_PASSWORD"),
    "database": os.getenv("MYSQL_ADDON_DB"),
}

USE_DB = all(DB_CFG.values())

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

CANDIDATE_GAMES = [
    os.path.join(BASE_DIR, "game_metadata.csv"),
    os.path.join(DATA_DIR, "game_metadata.csv"),
]

def _first_existing(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return None

GAMES_PATH = _first_existing(CANDIDATE_GAMES)

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    return df

def _ensure_cols(df: pd.DataFrame, cols, fill="") -> pd.DataFrame:
    for c in cols:
        if c not in df.columns:
            df[c] = fill
    return df

def _connect_mysql():
    import mysql.connector
    return mysql.connector.connect(
        host=DB_CFG["host"],
        port=DB_CFG["port"],
        user=DB_CFG["user"],
        password=DB_CFG["password"],
        database=DB_CFG["database"],
    )

def _load_games_from_db(limit: Optional[int] = None) -> pd.DataFrame:
    base_sql = """
        SELECT 
            game_id    AS id,
            name       AS title,
            genres,
            platforms,
            rating,
            released,
            cover_image,
            game_link,
            description
        FROM game_metadata
    """
    if limit and limit > 0:
        base_sql += f" LIMIT {int(limit)}"

    try:
        conn = _connect_mysql()
        df = pd.read_sql(base_sql, conn)
        conn.close()
    except Exception:
        return _load_games_from_csv(limit)

    df = _normalize_columns(df)
    df = _ensure_cols(df, ["id","title","genres","platforms","description","rating","released","cover_image","game_link"])
    df["id"] = df["id"].astype(str)
    for c in ["title","genres","platforms","description","cover_image","game_link"]:
        df[c] = df[c].astype(str).fillna("")
    return df

def _load_games_from_csv(nrows: Optional[int] = None) -> pd.DataFrame:
    if not GAMES_PATH:
        return pd.DataFrame()
    try:
        df = pd.read_csv(GAMES_PATH, nrows=nrows, low_memory=False, encoding_errors="ignore")
    except Exception:
        return pd.DataFrame()

    df = _normalize_columns(df)

    if "id" not in df.columns:
        for c in ("game_id", "itemid", "item_id"):
            if c in df.columns:
                df = df.rename(columns={c: "id"})
                break
    if "title" not in df.columns:
        for c in ("name", "game", "item_name", "title_name"):
            if c in df.columns:
                df = df.rename(columns={c: "title"})
                break
    if "description" not in df.columns:
        for c in ("desc", "summary", "about", "details"):
            if c in df.columns:
                df = df.rename(columns={c: "description"})
                break

    df = _ensure_cols(df, ["id","title","genres","platforms","description","rating","released","cover_image","game_link"])
    df["id"] = df["id"].astype(str)
    for c in ["title","genres","platforms","description","cover_image","game_link"]:
        df[c] = df[c].astype(str).fillna("")
    return df

def load_games(nrows: Optional[int] = None) -> pd.DataFrame:
    if USE_DB:
        return _load_games_from_db(limit=nrows)
    return _load_games_from_csv(nrows=nrows)

def get_dataset(nrows_games: Optional[int] = None) -> pd.DataFrame:
    return load_games(nrows_games)
