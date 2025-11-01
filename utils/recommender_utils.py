from __future__ import annotations
import os, sys, types, pickle
from typing import Any
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
        try:
            return fn(path)
        except Exception as e:
            errors.append(f"{fn.__name__}: {e}")
    return None

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
        if len(model) >= 2:
            out["vectorizer"], out["matrix"] = model[0], model[1]
        if len(model) >= 3 and isinstance(model[2], dict):
            out["title_to_idx"] = model[2]
        if len(model) >= 4:
            out["cosine"] = model[3]
        return out
    for attr in ["tfidf_matrix", "matrix", "X", "features_", "embeddings_"]:
        if hasattr(model, attr):
            out["matrix"] = getattr(model, attr)
            break
    for attr in ["cosine_", "cosine", "sims_"]:
        if hasattr(model, attr):
            out["cosine"] = getattr(model, attr)
            break
    for attr in ["title_to_idx", "indices_", "name_to_idx_"]:
        if hasattr(model, attr):
            out["title_to_idx"] = getattr(model, attr)
            break
    for attr in ["nn", "knn_", "neighbors_"]:
        if hasattr(model, attr):
            out["nn"] = getattr(model, attr)
            break
    for attr in ["vectorizer", "tfidf_", "vectorizer_"]:
        if hasattr(model, attr):
            out["vectorizer"] = getattr(model, attr)
            break
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
