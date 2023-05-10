# MongoDBからsummaryとsimilarityとcategoryを受け取っていい感じにくっつけるところ
import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pprint import pprint
import datetime
import setting
import scrapying
import chatgpt
import postblogger

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

def make_content(data):
    summary = data["summary"]
    similarity = data["similarity"]
    category = data["category"]
    
    if similarity:
        similarity_articles = []
        for id in similarity:
            article = rapidapi.find_one({"id": id}, {"title": 1, "url": 1})
            title = article["title"]
            url = article["url"]
            similarity_article = f"<li><a href='{url}'>{title}</a></li>"
            similarity_articles.append(similarity_article)
        similarity_content = "".join(similarity_articles)
        similarity_content = "<p>類似記事</p>" + "<ul>" + similarity_content + "</ul>"
    
    content = summary + similarity_content + category
    
    
    
    return content