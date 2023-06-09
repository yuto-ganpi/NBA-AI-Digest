# 製作途中です

# NBA-AI-Digest

- ChatGPT APIを利用した、海外のNBA関連のニュースサイトから最新記事を読み込んで要約して翻訳したものを表示するサイトです．

# URL
- https://nbaaimedia.blogspot.com/

# 概要

1. 主要メディアの最新記事取得
- RSS/Rapid APIから主要メディアの最新記事URLを取得
- 取得した記事のタイトル・本文を取得する
  - 全文が配信されるRSSはタイトル・本文を取得

2. 日本語の要約及び記事タイトル生成
- 原文のタイトル・本文をChatGPT APIに入力し要約を生成
- ChatGPTの回答に多少ルールベースでの修正を行う
- 出来上がった要約をChatGPT APIに入力し日本語に翻訳

3. ニュースのカテゴリー推定（予定）
- 原文タイトル及び2.の要約文をChatGPT APIに入力し
  ニュースのカテゴリーを推定（試合，記録，トレード，怪我，ドラフト，etc）

4. 記事のEmbeddingから、類似記事を探索（予定）
- 2.の要約文をOpenAI Embedding APIに入力し
  記事のEmbedding(ベクトル)を取得
- 他社の既報と酷似する記事は「後追い記事」扱いして、二次投稿（Twitterなど）には投稿しない

5. 記事をBlogger APIで投稿

6. 記事投稿をTwitterやDiscordなどで告知

# 使用技術

- Python 3.7.13
- MongoDB 6.0.5 (Atlas)
- ChatGPT API
- Blogger API
- Twitter API

# 全体像
![全体像](https://user-images.githubusercontent.com/56531106/235385039-9498e06e-69c3-4010-814c-89a87b50ccb1.png)


