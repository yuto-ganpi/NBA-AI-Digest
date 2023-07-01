# ChatGPT
import openai
import langid
import tiktoken
from tiktoken.core import Encoding
body_db = f"\
    I have just received new news.\
    \
    =========\
    title: \
    body: \
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
                
# lista = body_db.split()
# print(lista)
# stra = ' '.join(lista)
# print(stra)
# encoding: Encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
# tokens = encoding.encode(body_db)
# tokens_count = len(tokens)
# print(tokens_count)

a='"aaaa"'
b='bbbb'
print(a.strip('"'))
print(b.strip('"'))