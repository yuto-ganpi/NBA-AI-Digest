import os
import openai
import setting
import postblogger
import langid

def make_summary(article_url):
    openai.api_key = setting.OPENAI_API_KEY
    prompt = f"I will give you the URL of a news article about the NBA, so please summarize the news article in Japanese within 800 characters or less.\
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
                URL:\
                {article_url}\
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
        ]
    )
    

    text = response['choices'][0]['message']['content']
    print("text:", text)
    
    title = ""
    summary = ""

    title, summary = text.split("content:", 1)

    title = title.replace("title:", "")
    title = title.lstrip()
    summary = summary.lstrip()
    
    paragraphs = summary.split("\n\n")
    summary_p = ""
    for p in paragraphs:
        summary_p += "<p>" + p + "</p>"

    print("token:", response["usage"]["total_tokens"])
    
    return title, summary_p

def traslate(text, to_lang):
    openai.api_key = setting.OPENAI_API_KEY
    prompt = f"Please translate '{text}' to {to_lang}."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an excellent NBA reporter."},
            {"role": "user", "content": prompt},
        ]
    )

    translated = response['choices'][0]['message']['content']
    
    return translated
    
title_gpt, summary_gpt = make_summary("https://www.nba.com/news/5-takeaways-lakers-grizzlies-game-5")
title_lang = langid.classify(title_gpt)[0]
if title_lang != "ja":
    title_gpt = traslate(text=title_gpt, to_lang="Japanese")

summary_gpt = summary_gpt + "<p><a href='https://www.nba.com/news/5-takeaways-lakers-grizzlies-game-5'>引用元</a></p>"

client_id = setting.c_id
client_secret = setting.c_sr
postblogger.post_blogger(client_id=client_id, client_secret=client_secret, title=title_gpt, content=summary_gpt)