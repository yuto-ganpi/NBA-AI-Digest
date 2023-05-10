import openai
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import pymongo
from pprint import pprint
import datetime
import setting
import scrapying
import chatgpt
import postblogger
from openai.embeddings_utils import cosine_similarity

mongodbatlas_pass = setting.mongodbatlas_pass

uri = f'mongodb+srv://ganpi_atlas:{mongodbatlas_pass}@cluster0.cvknuco.mongodb.net/?retryWrites=true&w=majority'

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
    
db = client['nbaaimedia']
rapidapi = db['rapidapi']

openai.api_key = setting.OPENAI_API_KEY

# counter = 0
# for data in rapidapi.find({"source": "nba"}):
#     counter += 1
#     title_ja_db = data["title_ja"]
#     summary_db = data["summary"]
#     text = title_ja_db + summary_db
#     embedding = openai.Embedding.create(
#         input = text,
#         model = 'text-embedding-ada-002'
#         )["data"][0]["embedding"]
#     rapidapi.update_one({"_id": data["_id"]}, {"$set": {"embedding": embedding}})
#     if counter == 10:
#         break
    
data1 = rapidapi.find_one({"title": "Fox (finger) starts Game 5, scores 24 in loss"})
embedding1 = data1["embedding"]

data2_list = rapidapi.find({"source": "nba"}).skip(1).limit(9)
for data2 in data2_list:
    embedding2 = data2["embedding"]
    # コサイン類似度を計算する
    similarity = cosine_similarity(embedding1, embedding2)
    print(data2["title"], similarity)
    
# 初期化(外側からn番目を指定してその記事からm番前までの記事との類似度を計算し，lを超えていたら類似記事としてsimilarityフィールドにIDを追加する)
# m個の記事がたまるまでの処理まだ書いてない
def update_similarity(n, m=30, l=0.9):
    # 最新のEmbeddingを取得する
    nth_data = rapidapi.find().sort("_id", pymongo.ASCENDING).skip(n-1).limit(1)[0]
    embedding1 = nth_data["embedding"]
    
    # 最新のデータを除く最新からn件のEmbeddingを取得する
    data_list = rapidapi.find().sort("_id", pymongo.ASCENDING).skip(n).limit(n+m)

    similarity_list = []
    # 全てのデータの"similarity"を計算する
    for data2 in data_list:
        embedding2 = data2["embedding"]
        similarity = cosine_similarity(embedding1, embedding2)
        if similarity > l:
            similarity_list.append(data2["_id"])
    # "similarity"フィールドに計算結果を追加する
    rapidapi.update_one({"_id": nth_data["_id"]}, {"$set": {"similarity": similarity_list}})
    
# 最新の記事を取得したらまずEmbeddingを計算する
def cal_embedding(latest_data):
    title_ja_db = latest_data["title_ja"]
    summary_db = latest_data["summary"]
    text = title_ja_db + summary_db
    embedding = openai.Embedding.create(
        input = text,
        model = 'text-embedding-ada-002'
        )["data"][0]["embedding"]
    rapidapi.update_one({"_id": latest_data["_id"]}, {"$set": {"embedding": embedding}})
    
    return embedding

# 最新のn件のdataを取得する
def get_embedding_except_latest(n):
    data2_list = rapidapi.find().sort("_id", -1).skip(1).limit(n)

    return data2_list

# 最新の記事とそれ以前のn件前までのsimilarityを計算してsimilarityフィールドに追加する
# なかったらsimilarityフィールドはなし（でいいのか？）
def cal_similarity(latest_data, threshold_similarity):
    latest_embedding = latest_data["embedding"]
    # その記事から３０件前までのEmbeddingを取得
    data2_list = get_embedding_except_latest(n=30)
    
    similarity_list = []
    for data2 in data2_list:
        embedding2 = data2["embedding"]
        # コサイン類似度を計算する
        similarity = cosine_similarity(latest_embedding, embedding2)
        
        if similarity > threshold_similarity:
            similarity_list.append(data2["_id"])
            
    rapidapi.update_one({"_id": latest_data["_id"]}, {"$set": {"similarity": similarity_list}})
    
    