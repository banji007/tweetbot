from __future__ import print_function

import base64
import json
import boto3
import re
import emoji
#import nltk
#import sys


tablename = 'tweets-sentiment'

print('Loading function')
ssm = boto3.client('ssm')

#function to get variables from parameter store
def get_parameter(param_name):
    response = ssm.get_parameter(Name=param_name,WithDecryption=True)
    credentials = response['Parameter']['Value']
    return credentials
    
#retrieve parameters
#CONSUMER_KEY = get_parameter('/TWITTERBOT/CONSUMER_KEY')
#CONSUMER_SECRET = get_parameter('/TWITTERBOT/CONSUMER_SECRET')
#ACCESS_TOKEN = get_parameter('/TWITTERBOT/ACCESS_TOKEN')
#ACCESS_TOKEN_SECRET = get_parameter('/TWITTERBOT/ACCESS_TOKEN_SECRET')
AWS_KEY_ID = get_parameter('/TWITTERBOT/AWS_KEY_ID')
AWS_SECRET_ACCESS_KEY = get_parameter('/TWITTERBOT/AWS_SECRET_ACCESS_KEY')

# setup dynamodb table
session = boto3.Session(region_name='us-east-1',
                        aws_access_key_id=AWS_KEY_ID,
                        aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
dynamodb = session.resource('dynamodb')

table = dynamodb.Table(tablename)
comprehend = boto3.client('comprehend',  region_name='us-east-1')

def cleaner(tweet):
    tweet = re.sub("@[A-Za-z0-9]+","",tweet) #Remove @ sign
    tweet = re.sub(r"(?:\@|http?\://|https?\://|www)\S+", "", tweet) #Remove http links
    tweet = " ".join(tweet.split())
    tweet = ''.join(c for c in tweet if c not in emoji.UNICODE_EMOJI) #Remove Emojis
    tweet = tweet.replace("#", "").replace("_", " ") #Remove hashtag sign but keep the text
    #tweet = " ".join(w for w in nltk.wordpunct_tokenize(tweet) \
    #     if w.lower() in words or not w.isalpha())
    return tweet


def lambda_handler(event, context):
    #print(event)
    #1. Iterate over each record
    try:
        for record in event['Records']:
            #2. Handle event by type
            if record['eventName'] == 'INSERT':
                #3a. Get newImage content
                newImage = record['dynamodb']['NewImage']
                handle_insert(newImage)
            elif record['eventName'] == 'MODIFY':
                handle_modify(record)
            elif record['eventName'] == 'REMOVE':
                handle_remove(record)
        return "Success!"
    except Exception as e:
        print(e)
        return "Error"


def handle_insert(record):
    print("Handling INSERT Event")
    
    #print(record)
    content = record
    tweet = cleaner(content['text']['S'])
    #dict_data = base64.b64decode(tweet).decode('utf-8')
    #dict_data = base64.b64encode(tweet_data.encode('ascii')).decode('ascii').strip()
    
    #detect sentiment
    sentiment_all = comprehend.detect_sentiment(Text=tweet, LanguageCode='en')
    sentiment = sentiment_all['Sentiment']

    #print(content['sentiment'])
    positiveScore = sentiment_all['SentimentScore']['Positive']
    negativeScore = sentiment_all['SentimentScore']['Negative']
    totalScore = positiveScore - negativeScore
    
    #since - the scores are floating point - converting them to string with 5 decimals.
    s_positiveScore = "{0:.5f}".format(positiveScore)
    s_negativeScore = "{0:.5f}".format(negativeScore)
    s_totalScore = "{0:.5f}".format(totalScore)
    #print(s_positiveScore)
    #print(s_negativeScore)
    #print(s_totalScore)
    
    #creating data record of tweet with sentiment and total score
    data_record = {
        'tweet_id': content['tweet_id']['S'],
        'message': tweet,
        'sentiment': sentiment,
        'totalScore': s_totalScore
    }
    
    try:
        table.put_item(Item=data_record)
        print('Uploading tweet with sentiment score: {}'.format(content['text']['S']))
    except Exception as e:
        print(str(e))
    #return True

def handle_modify(record):
    print("Handling MODIFY Event")

def handle_remove(record):
    print("Handling REMOVE Event")

