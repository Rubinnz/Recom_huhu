import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

class NetflixStyleHybridRecommender:
    def __init__(self, cf_model, tfidf_vectorizer, cosine_sim, games_df, ratings_df, alpha=0.6, diversity_factor=0.1):
        self.cf_model = cf_model
        self.tfidf = tfidf_vectorizer
        self.cosine_sim = cosine_sim
        self.games_df = games_df.reset_index(drop=True)
        self.ratings_df = ratings_df
        self.alpha = alpha
        self.diversity_factor = diversity_factor
        self.scaler = MinMaxScaler((0, 1))
        self.scaler.fit(ratings_df[["rating"]])
        self.game_id_to_idx = {gid: idx for idx, gid in enumerate(self.games_df["game_id"])}
        self.idx_to_game_id = {idx: gid for gid, idx in self.game_id_to_idx.items()}
        self.game_id_to_name = dict(zip(self.games_df["game_id"], self.games_df["name"]))
        self.name_to_game_id = dict(zip(self.games_df["name"], self.games_df["game_id"]))
        self._compute_popularity()
        self.all_games = set(self.games_df["game_id"])
        self.all_users = set(self.ratings_df["user_id"])
    def _compute_popularity(self):
        popularity = self.ratings_df.groupby("game_id").agg({"rating": ["mean", "count"]}).reset_index()
        popularity.columns = ["game_id", "avg_rating", "num_ratings"]
        m = popularity["num_ratings"].quantile(0.25)
        C = popularity["avg_rating"].mean()
        popularity["popularity_score"] = ((popularity["num_ratings"] / (popularity["num_ratings"] + m)) * popularity["avg_rating"] + (m / (popularity["num_ratings"] + m)) * C)
        self.popularity_scores = dict(zip(popularity["game_id"], popularity["popularity_score"]))
    def predict_cf(self, user_id, game_id):
        try:
            return self.cf_model.predict(user_id, game_id).est
        except:
            return 3.0
    def get_content_similarity(self, game_id, liked_games):
        if game_id not in self.game_id_to_idx or not liked_games:
            return 0.0
        game_idx = self.game_id_to_idx[game_id]
        sims = []
        for liked in liked_games:
            if liked in self.game_id_to_idx:
                sims.append(self.cosine_sim[game_idx, self.game_id_to_idx[liked]])
        return np.mean(sims) if sims else 0.0
    def recommend(self, user_id=None, top_n=10, exclude_played=True, min_score=0.0):
        if user_id not in self.all_users:
            return self._recommend_cold_start(top_n)
        user_ratings = self.ratings_df[self.ratings_df["user_id"] == user_id]
        played_games = set(user_ratings["game_id"])
        liked_games = set(user_ratings[user_ratings["rating"] >= 4]["game_id"])
        candidates = self.all_games - played_games if exclude_played else self.all_games
        scores = {}
        for gid in candidates:
            cf_pred = self.predict_cf(user_id, gid)
            cf_score = self.scaler.transform([[cf_pred]])[0][0]
            cb_score = self.get_content_similarity(gid, liked_games)
            pop_score = self.popularity_scores.get(gid, 3.0) / 5.0
            final = self.alpha * cf_score + (1 - self.alpha) * cb_score + self.diversity_factor * pop_score
            if final >= min_score:
                scores[gid] = final
        top_games = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return [(self.game_id_to_name.get(g, "Unknown"), round(s, 4), g) for g, s in top_games]
    def _recommend_cold_start(self, top_n=10):
        popular = sorted(self.popularity_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return [(self.game_id_to_name.get(g, "Unknown"), round(s / 5, 4), g) for g, s in popular]
    def recommend_similar_games(self, game_name, top_n=10):
        if game_name not in self.name_to_game_id:
            return []
        gid = self.name_to_game_id[game_name]
        idx = self.game_id_to_idx[gid]
        sims = sorted(list(enumerate(self.cosine_sim[idx])), key=lambda x: x[1], reverse=True)[1:top_n + 1]
        return [(self.games_df.iloc[i]["name"], round(s, 4), self.games_df.iloc[i]["game_id"]) for i, s in sims]
    def get_user_profile(self, user_id):
        if user_id not in self.all_users:
            return {"error": "User not found"}
        user_ratings = self.ratings_df[self.ratings_df["user_id"] == user_id]
        profile = {"user_id": user_id, "total_games_played": len(user_ratings), "average_rating": round(user_ratings["rating"].mean(), 2), "favorite_games": [], "preferred_genres": []}
        favorites = user_ratings[user_ratings["rating"] >= 4].sort_values("rating", ascending=False)
        profile["favorite_games"] = [{"name": self.game_id_to_name.get(g, "Unknown"), "rating": float(r)} for g, r in zip(favorites["game_id"].head(5), favorites["rating"].head(5))]
        genres = []
        for g in favorites["game_id"]:
            row = self.games_df[self.games_df["game_id"] == g]
            if not row.empty:
                genres.extend(row.iloc[0]["genres"].split())
        if genres:
            from collections import Counter
            cnt = Counter(genres)
            profile["preferred_genres"] = [g for g, _ in cnt.most_common(5)]
        return profile
