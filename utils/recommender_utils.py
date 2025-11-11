import os, sys, types, pandas as pd, streamlit as st
from utils.netflix_style_hybrid import NetflixStyleHybridRecommender


def _ensure_stub(modname: str):
    if modname not in sys.modules:
        sys.modules[modname] = types.ModuleType(modname)
    mod = sys.modules[modname]
    if not hasattr(mod, "NetflixStyleHybridRecommender"):
        setattr(mod, "NetflixStyleHybridRecommender", NetflixStyleHybridRecommender)


@st.cache_resource(show_spinner=False)
def load_hybrid_model(path: str):
    import joblib
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model not found: {path}")
    _ensure_stub("utils.recommender_utils")
    _ensure_stub("main")
    _ensure_stub("__main__")
    model_pkg = joblib.load(path)
    if isinstance(model_pkg, dict) and "hybrid_recommender" in model_pkg:
        return model_pkg["hybrid_recommender"]
    return model_pkg


def _to_df_items(items):
    if not items:
        return pd.DataFrame(columns=["id", "title", "score"])
    if isinstance(items[0], (list, tuple)) and len(items[0]) == 3:
        df = pd.DataFrame(items, columns=["title", "score", "id"])
        df["id"] = df["id"].astype(str)
        return df[["id", "title", "score"]]
    return pd.DataFrame(columns=["id", "title", "score"])


def hybrid_top_recommendations(hybrid_model, user_id, n=10, exclude_game_ids=None):
    exclude_game_ids = set(map(str, exclude_game_ids or []))
    try:
        recs = hybrid_model.recommend(user_id=user_id, top_n=n)
        if not recs:
            recs = hybrid_model._recommend_cold_start(top_n=n)
        df = _to_df_items(recs)
        if not df.empty:
            df["id"] = df["id"].astype(str)
            return df[["id", "score"]]
    except Exception as e:
        st.warning(f"Recommendation error: {e}")
    return pd.DataFrame(columns=["id", "score"])


def hybrid_grouped_recommendations(hybrid_model, user_id, per_seed=5, exclude_game_ids=None):
    exclude_game_ids = set(map(str, exclude_game_ids or []))
    result = {}
    try:
        profile = hybrid_model.get_user_profile(user_id)
        favs = []
        if isinstance(profile, dict) and "favorite_games" in profile:
            favs = [g["name"] for g in profile["favorite_games"] if "name" in g]
        for g in favs:
            recs = hybrid_model.recommend_similar_games(g, top_n=per_seed)
            df = _to_df_items(recs)
            if not df.empty:
                df["id"] = df["id"].astype(str)
                result[g] = df[["id", "score"]]
    except Exception:
        return {}
    return result
