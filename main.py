from googleapiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow
from oauth2client        import tools,file
import argparse
import httplib2
import os
import sys
import setting
import postblogger

client_id = setting.c_id
client_secret = setting.c_sr

class main():
    # データ処理を実行する関数
    def data_processing():
        ...

    # データ処理を実行する関数で返ってきた{title, content, link_of_origin, created_at}をDBに格納する処理
    def store_in_database():
        ...

    # 要約の処理，In（content), Out(summary)
    def summarize():
        ...

    # 翻訳の処理, In(title, summary), Out(translation{title_ja, summary_ja, double_summary_ja})
    def translate():
        ...

    # Embedding, In(title+summary), Out(embedding_vector)
    def embed():
        ...

    # 類似度判定, In([embedding_vector]過去20件程度の記事のEmbedding_vector), Out(similarity)
    def similarity_check():
        ...

    # 重要度推定, In(title, summary), Out(importance)
    def estimate_importance():
        ...

    # カテゴリー推定, In(title, content), Out(categories)
    def categorize():
        ...

    # Bloggerへ投稿, In(translation{title_ja, summary_ja}, similarity, importance, categories), Out(link_of_blogger)
    def post_to_blogger():
        ...

    # Twitterへ投稿, In(translation{title_ja, double_summary_ja}, link_of_blogger), Out()
    def post_to_twitter():
        ...


 
 
if __name__ == '__main__':
    main(sys.argv, client_id, client_secret)