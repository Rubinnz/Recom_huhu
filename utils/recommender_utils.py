from __future__ import annotations
import os, sys, types, pickle, time
from typing import Iterable, Tuple, List, Any
import numpy as np
import pandas as pd
import streamlit as st

def _try_joblib_load(path: str):
    import joblib
    return joblib.load(path)

def _try_pickle_load(path: str):
    with open(path, "rb") as f:
        return pickle.load(f)

class _ModuleAliasUnpickler(pickle.Unpickler):
    CLASS_MAP = {("main", "ContentBasedRecommender"): type("ContentBasedRecommender", (object,), {})}
    def find_class(self, module, name):
        key = (module, name)
        if key in self.CLASS_MAP:
            return self.CLASS_MAP[key]
        return super().find_class(module, name)

def _try_pickle_with_alias(path: str):
    with open(path, "rb") as f:
        return _ModuleAliasUnpickler(f).load()

@st.cache_resource(show_spinner=False)
def load_cf_model(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Không tìm thấy CF model tại: {path}")
    errors = []
    for fn in (_try_joblib_load, _try_pickle_load, _try_pickle_with_alias):
        try:
            return fn(path)
        except Exception as e:
            errors.append(f"{fn.__name__}: {e}")
    raise RuntimeError("Không load được CF model (có thể file bị lỗi hoặc không đúng định dạng joblib/pickle).\n" + "\n".join(errors))

@st.cache_resource(show_spinner=False)
def load_cb_model(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Không tìm thấy CB model tại: {path}")
    if "main" not in sys.modules:
        fake_main = types.ModuleType("main")
        class ContentBasedRecommender: pass
        fake_main.ContentBasedRecommender = ContentBasedRecommender
        sys.modules["main"] = fake_main
    errors = []
    for fn in (_try_joblib_load, _try_pickle_load, _try_pickle_with_alias):
        try: return fn(path)
        except Exception as e: errors.append(f"{fn.__name__}: {e}")
    return None

def _surprise_predict_many(model: Any, user_id: str, item_ids: Iterable[str]) -> List[Tuple[str, float]]:
    preds = []
    for iid in item_ids:
        try:
            est = model.predict(str(user_id), str(iid)).est
            preds.append((str(iid), float(est)))
        except Exception:
            continue
    return preds

def _detect_cols(df: pd.DataFrame):
    lower = {c.lower(): c for c in df.columns}
    uid = lower.get("user_id") or lower.get("userid") or lower.get("user") or "user_id"
    iid = lower.get("game_id") or lower.get("item_id") or lower.get("itemid") or lower.get("id") or "game_id"
    rat = lower.get("rating") or lower.get("score") or "rating"
    ts  = lower.get("timestamp") or lower.get("time") or "timestamp"
    return uid, iid, rat, ts

def get_user_seen_items(ratings: pd.DataFrame | None, user_id: str) -> set[str]:
    if ratings is None or ratings.empty:
        return set()
    uid, iid, *_ = _detect_cols(ratings)
    sub = ratings[ratings[uid].astype(str) == str(user_id)]
    return set(sub[iid].astype(str).tolist())

def get_cf_recommendations(model: Any, user_id: str, games: pd.DataFrame, ratings: pd.DataFrame | None = None, topn: int = 10) -> pd.DataFrame:
    if model is None or games is None or games.empty:
        return pd.DataFrame()
    g = games.copy()
    if "id" not in g.columns: g["id"] = g.index.astype(str)
    if "title" not in g.columns: g["title"] = g["id"].astype(str)
    seen = get_user_seen_items(ratings, user_id)
    cand = g[~g["id"].astype(str).isin(seen)].copy()
    if cand.empty: return pd.DataFrame()
    scores = _surprise_predict_many(model, user_id, cand["id"].astype(str).tolist())
    if not scores: return pd.DataFrame()
    score_df = pd.DataFrame(scores, columns=["id", "score"])
    out = cand.merge(score_df, on="id", how="inner").sort_values("score", ascending=False)
    return out.head(topn)

def _build_fallback_cb_matrix(games: pd.DataFrame):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    texts = games["genres"].fillna("").astype(str).tolist()
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_df=0.95)
    X = vec.fit_transform(texts)
    sim = cosine_similarity(X)
    title_to_idx = {t: i for i, t in enumerate(games["title"].fillna("").astype(str).tolist())}
    return {"vectorizer": vec, "matrix": X, "cosine": sim, "title_to_idx": title_to_idx}

def _infer_cb_structure(model: Any):
    out = {"matrix": None, "cosine": None, "title_to_idx": None, "nn": None, "vectorizer": None}
    if isinstance(model, dict):
        out["matrix"] = model.get("matrix") or model.get("X") or model.get("tfidf")
        out["cosine"] = model.get("cosine")
        out["title_to_idx"] = model.get("title_to_idx") or model.get("indices")
        out["nn"] = model.get("nn")
        out["vectorizer"] = model.get("vectorizer")
        return out
    if isinstance(model, (list, tuple)):
        if len(model) >= 2: out["vectorizer"], out["matrix"] = model[0], model[1]
        if len(model) >= 3 and isinstance(model[2], dict): out["title_to_idx"] = model[2]
        if len(model) >= 4: out["cosine"] = model[3]
        return out
    for attr in ["tfidf_matrix", "matrix", "X", "features_", "embeddings_"]:
        if hasattr(model, attr): out["matrix"] = getattr(model, attr); break
    for attr in ["cosine_", "cosine", "sims_"]:
        if hasattr(model, attr): out["cosine"] = getattr(model, attr); break
    for attr in ["title_to_idx", "indices_", "name_to_idx_"]:
        if hasattr(model, attr): out["title_to_idx"] = getattr(model, attr); break
    for attr in ["nn", "knn_", "neighbors_"]:
        if hasattr(model, attr): out["nn"] = getattr(model, attr); break
    for attr in ["vectorizer", "tfidf_", "vectorizer_"]:
        if hasattr(model, attr): out["vectorizer"] = getattr(model, attr); break
    return out

def get_cb_recommendations(model: Any, games: pd.DataFrame, seed_title: str, topn: int = 10, text_col: str = "genres") -> pd.DataFrame:
    if games is None or games.empty:
        return pd.DataFrame()
    g = games.copy()
    if "title" not in g.columns:
        g["title"] = g["id"].astype(str)
    if text_col not in g.columns:
        text_col = "genres"
    g[text_col] = g[text_col].fillna("").astype(str)
    try:
        seed_idx = g.index[g["title"] == seed_title][0]
    except Exception:
        return pd.DataFrame()
    info = _infer_cb_structure(model) if model is not None else {}
    if info.get("matrix") is not None and info.get("vectorizer") is not None:
        from sklearn.metrics.pairwise import cosine_similarity
        X = info["matrix"]
        sim = cosine_similarity(X[seed_idx], X).ravel()
    else:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        vect = TfidfVectorizer(ngram_range=(1,2), min_df=2, max_df=0.95)
        X = vect.fit_transform(g[text_col])
        sim = cosine_similarity(X[seed_idx], X).ravel()
    order = np.argsort(sim)[::-1]
    order = [i for i in order if i != seed_idx][:topn]
    rec = g.iloc[order].copy()
    rec["score"] = sim[order]
    return rec

DEFAULT_RATINGS_PATH = "game_ratings.csv"

def _read_ratings_df(ratings_path: str = DEFAULT_RATINGS_PATH) -> pd.DataFrame:
    if os.path.exists(ratings_path) and os.path.getsize(ratings_path) > 0:
        try: df = pd.read_csv(ratings_path, sep=None, engine="python")
        except Exception: df = pd.read_csv(ratings_path, header=None, names=["game_id","user_id","rating","timestamp"])
    else:
        df = pd.DataFrame(columns=["game_id","user_id","rating","timestamp"])
    uid, iid, rat, ts = _detect_cols(df)
    for c in [uid, iid, rat, ts]:
        if c not in df.columns: df[c] = np.nan
    with pd.option_context("mode.chained_assignment", None):
        df[uid] = df[uid].astype(str).fillna("")
        df[iid] = df[iid].astype(str).fillna("")
        df[rat] = pd.to_numeric(df[rat], errors="coerce")
        df[ts]  = pd.to_numeric(df[ts], errors="coerce")
    return df

def get_existing_rating(user_id: str, item_id: str, ratings_path: str = DEFAULT_RATINGS_PATH) -> float | None:
    df = _read_ratings_df(ratings_path)
    uid, iid, rat, ts = _detect_cols(df)
    row = df[(df[uid] == str(user_id)) & (df[iid] == str(item_id))]
    if not row.empty:
        try: return float(row.iloc[-1][rat])
        except Exception: return None
    return None

def upsert_user_rating(user_id: str, item_id: str, rating: float, ratings_path: str = DEFAULT_RATINGS_PATH) -> pd.DataFrame:
    df = _read_ratings_df(ratings_path)
    uid, iid, rat, ts = _detect_cols(df)
    mask = (df[uid] == str(user_id)) & (df[iid] == str(item_id))
    df = df.loc[~mask].copy()
    new_row = pd.DataFrame([{uid: str(user_id), iid: str(item_id), rat: float(rating), ts: int(time.time())}])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(ratings_path, index=False)
    return df

def remove_user_rating(user_id: str, item_id: str, ratings_path: str = DEFAULT_RATINGS_PATH) -> pd.DataFrame:
    df = _read_ratings_df(ratings_path)
    uid, iid, *_ = _detect_cols(df)
    mask = (df[uid] == str(user_id)) & (df[iid] == str(item_id))
    df = df.loc[~mask].copy()
    df.to_csv(ratings_path, index=False)
    return df

def append_ratings_bulk(user_id: str, item_ids: list[str], rating: float = 4.5, ratings_path: str = DEFAULT_RATINGS_PATH) -> pd.DataFrame:
    df = _read_ratings_df(ratings_path)
    uid, iid, rat, ts = _detect_cols(df)
    rows = [{uid: str(user_id), iid: str(x), rat: float(rating), ts: int(time.time())} for x in item_ids]
    df = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
    df.to_csv(ratings_path, index=False)
    return df

def get_user_ids(ratings_path: str = DEFAULT_RATINGS_PATH) -> list[str]:
    df = _read_ratings_df(ratings_path)
    if df.empty: return []
    uid, *_ = _detect_cols(df)
    return sorted(df[uid].dropna().astype(str).unique().tolist())

def top_popular(games: pd.DataFrame, ratings: pd.DataFrame | None, topn: int = 10) -> pd.DataFrame:
    if games is None or games.empty: return pd.DataFrame()
    if ratings is not None and not ratings.empty:
        r = ratings.copy()
        uid, iid, rat, ts = _detect_cols(r)
        agg = r.groupby(iid, as_index=False).agg(rating_count=(rat,"count"), rating_mean=(rat,"mean"))
        denom = max(agg["rating_count"].max(), 1)
        agg["pop_score"] = 0.6*(agg["rating_count"]/denom) + 0.4*(agg["rating_mean"]/5.0)
        out = agg.sort_values(["pop_score","rating_count","rating_mean"], ascending=False)
        g = games.copy()
        if "id" not in g.columns: g["id"] = g.index.astype(str)
        out = out.merge(g, left_on=iid, right_on="id", how="left")
        return out.head(topn)
    g = games.copy()
    if "rating" in g.columns:
        g = g.sort_values(["rating","released"], ascending=[False, False], na_position="last")
    elif "released" in g.columns:
        g = g.sort_values(["released"], ascending=False, na_position="last")
    return g.head(topn)
