from googleapiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow
from oauth2client        import tools,file
import argparse
import httplib2
import os
import sys
import setting

client_id = setting.c_id
client_secret = setting.c_sr

def post_blogger(client_id, client_secret, title, content):
     
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
    body    = {
                  "kind": "blogger#post",
                  "id": "9113440773520455515",
                  "title": title,
                  "content": content
              }
    insert    = posts.insert(blogId='9113440773520455515', body=body)
    posts_doc = insert.execute()
 
    print(posts_doc)