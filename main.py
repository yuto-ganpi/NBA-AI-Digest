
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
# import datetime
import setting
from openai.embeddings_utils import cosine_similarity
import pymongo
# スクレイピング
import requests
from pprint import pprint
from readability.readability import Document
import urllib.request
import html2text
import re
# ChatGPT
import openai
import langid
import tiktoken
from tiktoken.core import Encoding
# カテゴリー推定
import ast
# 重複記事の確認
from bson.objectid import ObjectId
# Blogger
from googleapiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow
from oauth2client        import tools,file
import httplib2
# Twitter
import tweepy


# 環境変数
# MongoDB Atlas
mongodbatlas_pass = setting.mongodbatlas_pass

# Rapid API
r_api_key = setting.r_api_key

# Blogger
client_id = setting.c_id
client_secret = setting.c_sr

# Twitter
client_id_t = setting.client_id_t
client_secret_t = setting.client_secret_t
api_key_t = setting.api_key_t
api_secret_t = setting.api_secret_t
bearer_token_t = setting.bearer_token_t
access_token_t = setting.access_token_t
access_token_secret_t = setting.access_token_secret_t


# MongoDB Atlasとの接続
uri = f'mongodb+srv://ganpi_atlas:{mongodbatlas_pass}@cluster0.cvknuco.mongodb.net/?retryWrites=true&w=majority'

client = MongoClient(uri, server_api=ServerApi('1'))

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
    
db = client['nbaaimedia']
rapidapi = db['rapidapi']

openai.api_key = setting.OPENAI_API_KEY


# RapidAPIで最新記事を取得
def getbasicinfo():

    url = "https://nba-latest-news.p.rapidapi.com/articles"

    querystring = {"limit":"10"}

    headers = {
	    "X-RapidAPI-Key": r_api_key,
        "X-RapidAPI-Host": "nba-latest-news.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    basic_info = response.json()

    # pprint(basic_info)
    
    return basic_info

def extraction_body(url):
    
    # 実行
    html = urllib.request.urlopen(url).read()
    # 本文っぽい部分を抽出
    article = Document(html).summary()
    # htmlからmarkdown形式に変換
    body = html2text.html2text(article)
    body = body.replace('\n', '')
    body = body.replace('![]', '')
    body = re.sub(r'\(http.*?\)', '', body)
    # とりあえずコマンドラインに出力
    # print(body)
        
    return body

def remove_after_marker(text):
    # "* * *" を検索し、それを含む箇所以降の文章を削除する
    marker_regex = r"\* \* \*"
    match = re.search(marker_regex, text)
    if match:
        index = match.start()
        text = text[:index]
    
    return text

def get_unique_data(basic_info):
    existing_data_titles = [data['title'] for data in rapidapi.find({}, {"title": 1, "_id": 0}).sort("_id", -1).skip(0).limit(20)]
    print("existing_data_titles:", existing_data_titles)
    new_data = []
    for data in basic_info:
        if data['title'] not in existing_data_titles:
            new_data.append(data)
    
    return new_data

def insert_content(source, url):
    # データを取り出してcontentを作成し、contentカラムに追加
    body = extraction_body(url)
    body = remove_after_marker(body)
    rapidapi.update_one({"url": url}, {"$set": {"body": body}})
    return body

# ChatGPT API
def check_token_limit(prompt):
    encoding: Encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    tokens = encoding.encode(prompt)
    tokens_count = len(tokens)
    if tokens_count > 4096:
        return False
    return True   

def traslate(text, to_lang):
    prompt = f"Please translate '{text}' to {to_lang}.Please start writing from an answer suddenly without preface."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an excellent NBA reporter."},
            {"role": "user", "content": prompt},
        ]
    )

    translated = response['choices'][0]['message']['content']
    
    return translated

def split_text(text):
    if 'content:' in text:
        title, summary = text.split('content:', 1)
        return title.strip(), summary.strip()
    else:
        parts = text.split('\n\n', 1)
        if len(parts) > 1:
            return parts[0].strip(), parts[1].strip()
        else:
            return text.strip(), ''

def format_text(text):
    title, summary = split_text(text)

    title = title.replace("title:", "")
    title = title.lstrip()
    summary = summary.lstrip()
    
    return title, summary

def add_p_tag(summary):
    paragraphs = summary.split("\n\n")
    summary_p = ""
    for p in paragraphs:
        summary_p += "<p>" + p + "</p>"
        
    return summary_p

def delete_extra_token(body_db, max_tokens):
    encoding: Encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    body_db_encode = encoding.encode(body_db)
    body_db_tokens = len(body_db_encode)
    truncated_text = body_db
    if body_db_tokens < max_tokens:
        truncated_text = body_db
    else:
        # 文章を配列のリストにする
        body_db_list = body_db.split()
        # 指定されたトークン数以下になるまでトークンを結合
        truncated_list = []
        for str_item in body_db_list:
            truncated_str = ' '.join(truncated_list)
            count_encode = encoding.encode(truncated_str)
            count_tokens = len(count_encode)
            if count_tokens <= max_tokens:
                truncated_list.append(str_item)
            else:
                truncated_list.pop()
                truncated_text = ' '.join(truncated_list)
                break

    return truncated_text

def make_summary(article_title, article_body):
    article_body = delete_extra_token(article_body, 3600)
    prompt = f"Please summarize the news article in Japanese within 800 characters or less.\
                \
                Do not explain all the contents of the original article. End the story in three paragraphs, no matter how long the original text is.\
                \
                Follow the format below for the summary:\
                - First, write the article title in Japanese on the first line.\
                - Start writing with 'title:' and write it on one line.\
                - Start the body with 'content:'.\
                - Each paragraph must end with '\n\n.\
                \
                Please make sure to observe the two items related to compliance with laws and regulations.\
                If you fail to do so, we may face a lawsuit problem, and we may be on the verge of bankruptcy in the worst case.\
                1. Translating the entire text is copyright infringement and may lead to a lawsuit.\
                Please summarize the main points of the news concisely.\
                2. Writing speculations other than what is written in the article\
                is considered spreading rumors and may lead to a lawsuit problem.\
                Please do not write anything other than what is written in the news article.\
                \
                In addition, please observe all the following rules:\
                - Do not mention that you are using the following rules in the article.\
                - All service names and personal names should be written in English.\
                - Do not repeat the same sentence/paragraph multiple times.\
                - Please break up the paragraphs frequently.\
                - Make sure to summarize within three paragraphs.\
                - A link to the reference article is not necessary.\
                - You do not need to provide information about the reference article.\
                - Paragraph numbers are not required.\
                - For reference, some NBA terminology is listed below.\
                  - Game 5: 第5戦\
                \
                =========\
                \
                title:\
                {article_title}\
                \
                text:\
                {article_body}\
                \
                =========\
                \
                Write in Japanese from here.\
                Please write concisely within 800 characters."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    

    text = response['choices'][0]['message']['content']
    print("make_summary_text:", text)
    
    title, summary = format_text(text)
    
    # タイトルが日本語訳されていないとき再度翻訳にかける
    title_lang = langid.classify(title)[0]
    if title_lang != "ja":
        title = traslate(text=title, to_lang="Japanese")
    
    summary_p = add_p_tag(summary)

    print("token:", response["usage"]["total_tokens"])
    
    # summary_pにsimilarityを付けたものがcontentになる
    return title, summary_p

def make_double_summary(article_title, article_summary, article_url):
    prompt = f"Please create a text to be posted on Twitter with 70 characters or less in Japanese.\
                \
                Do not explain all the contents of the original article. End the story in three paragraphs, no matter how long the original text is.\
                \
                Follow the format below for the text:\
                - Please start writing from the posted text suddenly without any preamble.\
                \
                Please make sure to observe the two items related to compliance with laws and regulations.\
                If you fail to do so, we may face a lawsuit problem, and we may be on the verge of bankruptcy in the worst case.\
                1. Translating the entire text is copyright infringement and may lead to a lawsuit.\
                Please summarize the main points of the news concisely.\
                2. Writing speculations other than what is written in the article\
                is considered spreading rumors and may lead to a lawsuit problem.\
                Please do not write anything other than what is written in the news article.\
                \
                In addition, please observe all the following rules:\
                - Do not mention that you are using the following rules in the article.\
                - All service names and personal names should be written in English.\
                - Do not repeat the same sentence/paragraph multiple times.\
                - Please break up the paragraphs frequently.\
                - A link to the reference article is not necessary.\
                - You do not need to provide information about the reference article.\
                - Paragraph numbers are not required.\
                - For reference, some NBA terminology is listed below.\
                  - Game 5: 第5戦\
                \
                =========\
                \
                title:\
                {article_title}\
                \
                text:\
                {article_summary}\
                \
                =========\
                \
                Write in Japanese from here.\
                Please write concisely within 70 characters."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    

    double_summary = response['choices'][0]['message']['content']
    print("make_double_summary:", double_summary)
        
    double_summary = double_summary + f"\n{article_url}"

    print("tweet:", double_summary)

    print("token:", response["usage"]["total_tokens"])
    
    # summary_pにsimilarityを付けたものがcontentになる
    return double_summary


# カテゴリー推定
# ChatGPTを用いて類似記事を判断  
def make_prompt_category(article_title, article_body):
    article_body = delete_extra_token(article_body, 3700)
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


# Embedding
def cal_embedding(title_ja, summary):
    text = title_ja + summary
    embedding = openai.Embedding.create(
        input = text,
        model = 'text-embedding-ada-002'
        )["data"][0]["embedding"]
    
    return embedding


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
        text = text.strip('"')
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

def make_json_dup_list(dup_list):
    dup_title_url = []
    for data_id in dup_list:
        data = rapidapi.find_one({"_id": data_id})
        if data:
            dup_title_url.append([data["article_url"], data["title_ja"]])
                
    return dup_title_url


# 記事投稿
def post_blogger(client_id, client_secret, title:str, content: str, category: list, dup_title_url, reference_url, reference_title):
     
    # flowオブジェクトの生成
    client_id     = client_id
    client_secret = client_secret
    scope         = 'https://www.googleapis.com/auth/blogger'
    redirect_uri  = 'urn:ietf:wg:oauth:2.0:oob'
    flow          = OAuth2WebServerFlow(client_id=client_id,
                                        client_secret=client_secret,
                                        scope=scope,
                                        redirect_uri=redirect_uri)
 
    # strageオブジェクトの生成、読み込み
    storage     = file.Storage(__file__ + '.dat') # 認証資格情報の保存ファイル名
    credentials = storage.get()                   # 認証資格情報の読み込み
 
    # 認証資格情報の取得（保存済みの資格情報がない場合）
    if credentials is None or credentials.invalid:
        credentials = tools.run_flow(flow, storage)
 
    http = credentials.authorize(http = httplib2.Http())
 
    service = build('blogger', 'v3', http=http)
    posts   = service.posts()
    
    # labelsで与えるcategoryはlist形式ではなく,で区切るだけの文字列で受け付けている
    category_str = ', '.join(category)
    
    # 重複記事の場合
    if(dup_title_url):
        li_script = ""
        for item in dup_title_url:
            url = item[0]
            title = item[1]
            li_script += f'<li><a href="{url}">{title}</a></li>'
        
        title = "【類似記事有】" + title
        content = f'\n\
<h3>関連記事一覧</h3>\n\
    <ul>\n\
        {li_script}\n\
    </ul>\n\
\n' + content

    content = content + f"<p>引用元：<a href='{reference_url}'>{reference_title}</a></p>"
    
    body    = {
                  "kind": "blogger#post",
                  "id": "9113440773520455515",
                  "title": title,
                  "content": content,
                  "labels": category_str,
              }
    insert    = posts.insert(blogId='9113440773520455515', body=body)
    posts_doc = insert.execute()
 
    print(posts_doc)
    
    article_url = posts_doc['url']
    article_title = posts_doc['title']
    
    return article_url, article_title


# Twitter
def clientInfo():
    client = tweepy.Client(bearer_token = bearer_token_t,
                           consumer_key = api_key_t,
                           consumer_secret = api_secret_t,
                           access_token = access_token_t,
                           access_token_secret = access_token_secret_t,
                           )
    
    return client

def createTweet(message):
    tweet = clientInfo().create_tweet(text=message)
    return tweet


def main():
    basic_info = getbasicinfo()
    new_data = get_unique_data(basic_info)
    print("new_article: \n", new_data)
    
    if new_data:
        # ここからメインの処理
        for new_article in new_data:
            source = new_article["source"]
            if source != "nba_canada":
                title_db = new_article["title"]
                reference_url_db = new_article["url"]
                body_db = insert_content(source, reference_url_db)
                
                # 要約の作成
                title_gpt, summary_gpt = make_summary(article_title=title_db, article_body=body_db)
                
                # カテゴリー分類
                prompt_category = make_prompt_category(article_title=title_db, article_body=body_db)
                category_list = make_category(prompt_category)
                
                # embedding保存
                embedding_array = cal_embedding(title_ja=title_gpt, summary=summary_gpt)
                
                similarity_id_list = []
                # 重複判定
                previous_data_list = rapidapi.find({"source": {"$ne": "nba_canada"}}).sort("_id", -1).skip(0).limit(15)
                if previous_data_list:
                    for previous_data in previous_data_list:
                        # print("previous_data_count")
                        previous_embedding = previous_data["embedding"]
                        # コサイン類似度を計算する
                        similarity = cosine_similarity(embedding_array, previous_embedding)
                        if  similarity > 0.9:
                            similarity_id_list.append(previous_data["_id"])
                
                dup_list = []
                dup_title_url = ""
    
                if similarity_id_list:
                    # print("maku_promptする前:", similarity_id_list)
                    dup_list = make_dup_list(title_db=title_db, body_db=body_db, similarity_id_list=similarity_id_list, summary_ja=summary_gpt)
                    
                    if dup_list:
                        dup_title_url = make_json_dup_list(dup_list)
                
                # 記事投稿
                article_url, article_title = post_blogger(client_id=client_id, client_secret=client_secret, title=title_gpt, content=summary_gpt, 
                                                          category=category_list, dup_title_url=dup_title_url, reference_url=reference_url_db, reference_title=title_db)
                
                double_summary = ""
                # Tweet
                # if "類似記事有" not in article_title:
                #     # さらに要約する関数
                #     double_summary = make_double_summary(article_title=title_gpt, article_summary=summary_gpt, article_url=article_url)
                #     createTweet(double_summary)
                    
                new_article_document = {
                    "title": title_db,
                    "url": reference_url_db,
                    "source": source,
                    "body": body_db,
                    "summary": summary_gpt,
                    "title_ja": title_gpt,
                    "category": category_list,
                    "embedding": embedding_array,
                    "similarity_id_list": similarity_id_list,
                    "dup_list": dup_list,
                    "article_url": article_url,
                    "article_title": article_title,
                    "tweet": double_summary,
                }
                rapidapi.insert_one(new_article_document)
        
    return


main()