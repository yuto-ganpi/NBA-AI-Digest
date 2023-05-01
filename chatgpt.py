import os
import openai
import setting
import postblogger

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
                - End the paragraph with '<br /><br />'\
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
        ]
    )
    

    text = response['choices'][0]['message']['content'].lstrip()
    print("text:", text)
    
    # title_a, content_a = text.split("\n\n", 1)

    print("token:", response["usage"]["total_tokens"])
    
    # return title_a, content_a
    
title_b, content_b = make_summary("Fox (finger) starts Game 5, scores 24 in loss", "De’Aaron Fox posted 38 points, nine rebounds and five assists in Sunday’s Game4 loss.Sacramento star guard De’Aaron Fox followed through Wednesday after saying heplanned to play in Game 5 of the Kings’ [first-roundseries] against theGolden State Warriors while dealing with a fractured finger on his shootinghand.Playing 42 minutes, Fox scored 24 points while adding seven rebounds, nineassists, two steals and a block. The finger did seem to limit his efficiency,as he shot 9-for-25 and committed six turnovers in [the 123-116loss].The Kings said Monday night that X-rays revealed an avulsion fracture on Fox’sleft index finger.Fox remained in the game after the injury and even made a key 3-pointer in theclosing minute before Sacramento [lost 126-125]. Fox passed out of a double team on the final possessionand the Kings lost when Harrison Barnes missed a 3-pointer at the buzzer.The Warriors now lead the series headed into Game 6 at Chase Center.Fox has emerged as a star in his first trip to the postseason, averaging 31.5points, seven assists and six rebounds through six games.His 38 points in a Game 1 win were tied for the second most for a player inhis postseason debut and his 126 points so far are tied for the sixth most forany player in his first four career playoff games.Fox had 38 points, nine rebounds and five assists in the Game 4 loss.")


client_id = setting.c_id
client_secret = setting.c_sr
postblogger.post_blogger(client_id=client_id, client_secret=client_secret, title=title_b, content=content_b)