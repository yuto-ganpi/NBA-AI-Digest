from googleapiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow
from oauth2client        import tools,file
import argparse
import httplib2
import os
import sys
import setting
from bson.objectid import ObjectId

client_id = setting.c_id
client_secret = setting.c_sr

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
    