import joblib

model_pkg = joblib.load("hybrid_model.pkl")
recommender = model_pkg["hybrid_recommender"]

# Get recommendations:
recommendations = recommender.recommend(user_id="user_4971", top_n=10)
for i in enumerate(recommendations, 1):
    print(i)
