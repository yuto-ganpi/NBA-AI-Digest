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
import ast

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



# ChatGPTを用いて類似記事を判断  
def make_prompt_category(article_title, article_body):
    prompt = f"\
    I have just received new news.\
    \
    =========\
    title: {article_title}\
    body: {article_body}\
    =========\
    \
    Please categorize this article.\
    please observe all the following rules:\
    - Please select only those that are at least 80% certain\
    - Minimum 1 category\
    - Use the following pre-defined groups of categories when categorizing.\
    \
    =========\
    [\
    'Trade/contract',\
    'Injury/health',\
    'Rule change',\
    'Regular season',\
    'Preseason',\
    'Playoffs',\
    'Analysis',\
    'Off-court',\
    'All-Star',\
    'Draft',\
    'Individual performance',\
    'Team performance',\
    'Award',\
    'Referee',\
    'SNS',\
    'Prediction',\
    'Fashion',\
    'Business/economy',\
    'Stadium',\
    'G-League',\
    'NCAA',\
    'Technology',\
    'Game',\
    'Workout',\
    'Tactics',\
    'Product',\
    'Sports-science'\
    ]\
    =========\
    \
    Do not classify into categories other than the reference ones.\
    \
    \
    Please answer this item in the following list format.\
    \
    =========\
    ['category1', 'category2', 'category3']\
    =========\
    "
    
    return prompt

def make_category(prompt: str) -> list:
    openai.api_key = setting.OPENAI_API_KEY
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    

    category_list = response['choices'][0]['message']['content']
    category_list = ast.literal_eval(category_list)
    print("list:", category_list)
    
    return category_list

# 試し
# counter = 0
# for data in rapidapi.find({"source": "nba"}):
#     counter += 1
#     title_db = data["title"]
#     body_db = data["body"]
#     prompt = make_prompt_category(article_title=title_db, article_body=body_db)
#     category_list = make_category(prompt)
#     rapidapi.update_one({"_id": data["_id"]}, {"$set": {"category": category_list}})
    
#     if counter == 2:
#         break