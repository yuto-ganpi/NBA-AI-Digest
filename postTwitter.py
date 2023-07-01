import base64
import hashlib
import os
import sys
import setting
import re
import json
import requests
import tweepy
from requests.auth import AuthBase, HTTPBasicAuth
from requests_oauthlib import OAuth2Session
from pprint import pprint


# 認証準備
client_id_t = setting.client_id_t
client_secret_t = setting.client_secret_t
api_key_t = setting.api_key_t
api_secret_t = setting.api_secret_t
bearer_token_t = setting.bearer_token_t
access_token_t = setting.access_token_t
access_token_secret_t = setting.access_token_secret_t

def clientInfo():
    client = tweepy.Client(bearer_token = bearer_token_t,
                           consumer_key = api_key_t,
                           consumer_secret = api_secret_t,
                           access_token = access_token_t,
                           access_token_secret = access_token_secret_t,
                           )
    
    return client

def createTweet(message):
    tweet = clientInfo().create_tweet(text=message)
    return tweet