import os
import openai
import setting
import postblogger
import langid
import tiktoken
from tiktoken.core import Encoding

def check_token_limit(prompt):
    encoding: Encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    tokens = encoding.encode(prompt)
    tokens_count = len(tokens)
    if tokens_count > 4096:
        return False
    return True   

def traslate(text, to_lang):
    openai.api_key = setting.OPENAI_API_KEY
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

def make_summary(article_title, article_body):
    openai.api_key = setting.OPENAI_API_KEY
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
    openai.api_key = setting.OPENAI_API_KEY
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