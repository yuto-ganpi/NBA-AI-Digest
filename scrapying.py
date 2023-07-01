import requests
from pprint import pprint
from readability.readability import Document
import urllib.request
import html2text
import re


# RapidAPIで最新記事を取得
def rapidapi():

    url = "https://nba-latest-news.p.rapidapi.com/articles"

    querystring = {"limit":"10"}

    headers = {
	    "X-RapidAPI-Key": "c8cc1dee43msh75869d075130888p154ffajsn2472eec87dce",
        "X-RapidAPI-Host": "nba-latest-news.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    basic_info = response.json()

    pprint(basic_info)
    
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


a = rapidapi()
print(a, type(a))