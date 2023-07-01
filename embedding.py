# Chatgptで判断するときに重複しているかいないかの2値でするか重複率でするか

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
import json
import uuid
from bson.objectid import ObjectId
import tiktoken
from tiktoken.core import Encoding



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

# 試し
# counter = 0
# for data in rapidapi.find({"source": {"$ne": "nba_canada"}}):
#     counter += 1
#     title_ja_db = data["title"]
#     summary_db = data["summary"]
#     text = title_ja_db + summary_db
#     embedding = openai.Embedding.create(
#         input = text,
#         model = 'text-embedding-ada-002'
#         )["data"][0]["embedding"]
#     rapidapi.update_one({"_id": data["_id"]}, {"$set": {"embedding": embedding}})
#     if counter == 20:
#         break


# # 試し
# counter = 0
# for data in rapidapi.find({"source": {"$ne": "nba_canada"}}):
#     counter += 1
#     title_db = data["title"]
#     embedding_db = data["embedding"]
#     previous_data_list = rapidapi.find({"source": {"$ne": "nba_canada"}}).skip(counter).limit(counter+8)
#     for previous_data in previous_data_list:
#         previous_embedding = previous_data["embedding"]
#         # コサイン類似度を計算する
#         similarity = cosine_similarity(embedding_db, previous_embedding)
#         print(f"{title_db}:", previous_data["title"], similarity)
    
#     # rapidapi.update_one({"_id": data["_id"]}, {"$set": {"similarity": similarity}})
#     if counter == 10:
#         break


def check_token_limit(prompt):
    encoding: Encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    tokens = encoding.encode(prompt)
    tokens_count = len(tokens)
    if tokens_count > 4096:
        return False
    return True    
    
# 初期化(n番目を指定してその記事からm番前までの記事との類似度を計算し，lを超えていたら類似記事としてsimilarityフィールドにIDを追加する)
# m個の記事がたまるまでの処理まだ書いてない
def update_similarity(n, m=30, l=0.9):
    # 最新のEmbeddingを取得する
    nth_data = rapidapi.find().sort("_id", pymongo.ASCENDING).skip(n-1).limit(1)[0]
    latest_embedding = nth_data["embedding"]
    
    # 最新のデータを除く最新からn件のEmbeddingを取得する
    previous_data_list = rapidapi.find().sort("_id", pymongo.ASCENDING).skip(n).limit(n+m)

    similarity_id_list = []
    # 全てのデータの"similarity"を計算する
    for previous_data in previous_data_list:
        previous_embedding = previous_data["embedding"]
        similarity = cosine_similarity(latest_embedding, previous_embedding)
        if similarity > l:
            similarity_id_list.append(previous_data["_id"])
    # "similarity"フィールドに計算結果を追加する
    rapidapi.update_one({"_id": nth_data["_id"]}, {"$set": {"similarity_id_list": similarity_id_list}})

# ここから下は最新の記事取得後
# 最新の記事を取得したらまずEmbeddingを計算する
def cal_embedding(title_ja, summary):
    text = title_ja + summary
    embedding = openai.Embedding.create(
        input = text,
        model = 'text-embedding-ada-002'
        )["data"][0]["embedding"]
    
    return embedding

# 最新のn件のdataを取得する
def get_embedding_except_latest(n):
    previous_data_list = rapidapi.find().sort("_id", -1).skip(1).limit(n)

    return previous_data_list

# 最新の記事とそれ以前のn件前までのsimilarityを計算してthreshold_similarityを超える記事のidをsimilarityフィールドに追加する
# この後類似記事のリストを渡して過去の記事と重複しているかをGPT4に判断させる
def cal_similarity(latest_data, threshold_similarity):
    latest_embedding = latest_data["embedding"]
    # その記事から３０件前までのEmbeddingを取得
    previous_data_list = get_embedding_except_latest(n=30)
    
    similarity_id_list = []
    for previous_data in previous_data_list:
        previous_embedding = previous_data["embedding"]
        # コサイン類似度を計算する
        similarity = cosine_similarity(latest_embedding, previous_embedding)
        
        if similarity > threshold_similarity:
            similarity_id_list.append(previous_data["_id"])
            
    rapidapi.update_one({"_id": latest_data["_id"]}, {"$set": {"similarity_id_list": similarity_id_list}})
    
    return

# 
# ChatGPTを用いて類似記事を判断  
def make_prompt_similarity_en(article_title, article_body, similarity_id_list_item):
    # article_title = latest_data["title"]
    # article_body = latest_data["body"]
    # similarity_id_list = latest_data["similarity_id_list"]
    body = rapidapi.find_one({"_id": similarity_id_list_item}, {"body": 1})
    similarity_comparator = f"id: {similarity_id_list_item}, body: {body}"
    
    print("similarity_comparator:", similarity_comparator)
    
    prompt = f'\
    I have just received new news.\
    \
    =========\
    title: {article_title}\
    content: {article_body}\
    =========\
    \
    On the other hand, there is similar article about this news.\
    Compare with this article to determine if the new news contains new facts.\
    \
    Similar article is determined to be similar and listed using the Embedding expression.\
    New news may contain new facts or new analysis not included in similar article.\
    In that case, do not consider it a duplicate article.\
    \
    Do not jump to conclusions at the beginning, but think step-by-step first.\
    \
    =========\
    Candidate for similar article:\
    {similarity_comparator}\
    =========\
    \
    If you have a similar article, return the id of that article in string format as follows\
    \
    =========\
    \
    "{similarity_id_list_item}"\
    \
    =========\
    \
    If you do not see a similar article, please return the following.\
    \
    =========\
    \
    "null"\
    \
    =========\
    '
    
    return prompt

def make_prompt_similarity_ja(article_title, article_summary_ja, similarity_id_list_item):
    # article_title = latest_data["title"]
    # article_body = latest_data["body"]
    # similarity_id_list = latest_data["similarity_id_list"]
    summary_ja = rapidapi.find_one({"_id": similarity_id_list_item}, {"summary": 1})
    similarity_comparator = f"id: {similarity_id_list_item}, summary: {summary_ja}"
    
    print("similarity_comparator:", similarity_comparator)
    
    prompt_ja = f'\
    I have just received new news.\
    \
    =========\
    title: {article_title}\
    content: {article_summary_ja}\
    =========\
    \
    On the other hand, there is similar article about this news.\
    Compare with this article to determine if the new news contains new facts.\
    \
    Similar article is determined to be similar and listed using the Embedding expression.\
    New news may contain new facts or new analysis not included in similar article.\
    In that case, do not consider it a duplicate article.\
    \
    Do not jump to conclusions at the beginning, but think step-by-step first.\
    \
    =========\
    Candidate for similar article:\
    {similarity_comparator}\
    =========\
    \
    If you have a similar article, return the id of that article in string format as follows\
    \
    =========\
    \
    "{similarity_id_list_item}"\
    \
    =========\
    \
    If you do not see a similar article, please return the following.\
    \
    =========\
    \
    "null"\
    \
    =========\
    \
    Please make sure to answer with either "{similarity_id_list_item}" or "null".\
    '
    
    return prompt_ja

def make_dup_list_item(prompt):
    openai.api_key = setting.OPENAI_API_KEY
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    

    text = response['choices'][0]['message']['content']
    
    # このtextはstringなのでjson形式に変える，
    if text=="null":
        text=None
    else:
        text = ObjectId(text)
    
    # 返り値はjson型
    return text

def make_dup_list(title_db, body_db, similarity_id_list, summary_ja):
    dup_list = []
    for similarity_id_list_item in similarity_id_list:
        prompt_dup = make_prompt_similarity_en(title_db, body_db, similarity_id_list_item)
        
        if check_token_limit(prompt_dup):
            pass
        else:
            print("プロンプトが上限トークン数を超えています。長さを調整してください。")
            prompt_dup = make_prompt_similarity_ja(title_db, summary_ja, similarity_id_list_item)
            
        dup_list_item = make_dup_list_item(prompt_dup)
        if dup_list_item:
            dup_list.append(dup_list_item)
    print("dup_list:", dup_list)
    return dup_list

def generate_unique_post_id():
    # UUIDを生成し、ハイフンを除去して小文字に変換
    unique_id = str(uuid.uuid4()).replace('-', '').lower()
    
    # 一意の8文字のpostIdを取得
    post_id = unique_id[:8]
    
    return post_id


def make_json_dup_list(dup_list):
    dup_title_url = []
    for data_id in dup_list:
        data = rapidapi.find_one({"_id": data_id})
        if data:
            dup_title_url.append([data["article_url"], data["title_ja"]])
                
    return dup_title_url