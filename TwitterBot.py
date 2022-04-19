import tweepy
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy import API
from tweepy import Cursor
import boto3
import os

ssm = boto3.client('ssm')
TEXT = os.environ.get('TEXT')
HANDLES = os.environ.get('HANDLES')


#this handles the authentication to the twitter streaming API
class Authentication():
  def __init__(self,CONSUMER_KEY,CONSUMER_SECRET,ACCESS_TOKEN,ACCESS_TOKEN_SECRET):
    self.CONSUMER_KEY = CONSUMER_KEY
    self.CONSUMER_SECRET = CONSUMER_SECRET
    self.ACCESS_TOKEN = ACCESS_TOKEN
    self.ACCESS_TOKEN_SECRET = ACCESS_TOKEN_SECRET

  def authenticate(self):
    auth = OAuthHandler(self.CONSUMER_KEY, self.CONSUMER_SECRET)
    auth.set_access_token(self.ACCESS_TOKEN, self.ACCESS_TOKEN_SECRET)

    return auth

class TwitterClient():
  def __init__(self,CONSUMER_KEY,CONSUMER_SECRET,ACCESS_TOKEN,ACCESS_TOKEN_SECRET,twitter_user=None,):
    self.CONSUMER_KEY = CONSUMER_KEY
    self.CONSUMER_SECRET = CONSUMER_SECRET
    self.ACCESS_TOKEN = ACCESS_TOKEN
    self.ACCESS_TOKEN_SECRET = ACCESS_TOKEN_SECRET
    
    self.auth = Authentication(self.CONSUMER_KEY,self.CONSUMER_SECRET,self.ACCESS_TOKEN,self.ACCESS_TOKEN_SECRET).authenticate()
    self.twitter_client = API(self.auth)
    self.twitter_user = twitter_user

  def get_timeline_tweets(self,num_tweets):
    tweets = []
    for tweet in Cursor(self.twitter_client.user_timeline,id =self.twitter_user ).items(num_tweets):
      tweets.append(tweet)
    
    return tweets

  def get_twitter_api(self):
    return self.twitter_client

  def get_friend_list(self,num_friends):
    friends = []
    for friend in Cursor(self.twitter_client.friends,id =self.twitter_user).items(num_friends):
      friends.append(friend)
    
    return friends

  def get_hometimeline_tweets(self,num_tweets):
    home_tweets = []
    for tweet in Cursor(self.twitter_client.home_timeline).items(num_tweets):
      home_tweets.append(tweet)
    
    return home_tweets


def lambda_handler(event, context):
    
    #retrieve parameters
    ACCESS_TOKEN = get_parameter('ACCESS_TOKEN')
    ACCESS_TOKEN_SECRET = get_parameter('ACCESS_TOKEN_SECRET')
    CONSUMER_SECRET = get_parameter('CONSUMER_SECRET')
    CONSUMER_KEY = get_parameter('CONSUMER_KEY')
    
    #authenticate tweepy
    auth = Authentication(CONSUMER_KEY,CONSUMER_SECRET,ACCESS_TOKEN,ACCESS_TOKEN_SECRET).authenticate()
    twitterApi = tweepy.API(auth, wait_on_rate_limit=True)
    
    accounts = HANDLES.split(",")
    
    for account in accounts:
      twitter_client = TwitterClient(CONSUMER_KEY,CONSUMER_SECRET,ACCESS_TOKEN,ACCESS_TOKEN_SECRET,account)
      user_tweets=twitter_client.get_timeline_tweets(2)
      
      user_id = user_tweets[0].id
      
      for tweet in user_tweets:
        TWEET_ID = str(tweet.id)
        tweet = twitterApi.get_status(TWEET_ID)
        print(tweet.text)
        comment = TEXT
        try:
          res = twitterApi.update_status(comment, in_reply_to_status_id=TWEET_ID)
        except:
          print("No New Tweet")

#function to get variables from parameter store
def get_parameter(param_name):
    response = ssm.get_parameter(Name=param_name,WithDecryption=True)
    credentials = response['Parameter']['Value']
    return credentials 
