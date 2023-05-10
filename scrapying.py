import requests
from pprint import pprint
from readability.readability import Document
import urllib.request
import html2text
import re

def rapidapi():

    url = "https://nba-latest-news.p.rapidapi.com/articles"

    headers = {
        "X-RapidAPI-Key": "c8cc1dee43msh75869d075130888p154ffajsn2472eec87dce",
        "X-RapidAPI-Host": "nba-latest-news.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers)
    basic_info = response.json()

    pprint(basic_info)
    
    return basic_info

def make_content(url):
    # 実行
    html = urllib.request.urlopen(url).read()
    # 本文っぽい部分を抽出
    article = Document(html).summary()
    # htmlからmarkdown形式に変換
    content = html2text.html2text(article)
    content = content.replace('\n', '')
    content = content.replace('![]', '')
    content = re.sub(r'\(http.*?\)', '', content)
    # とりあえずコマンドラインに出力
    print(content)
    
    return content

make_content("https://www.nba.com/news/5-takeaways-lakers-grizzlies-game-5")