import sys
import tweepy
from src.pipeline import MyPipeline

class TwitterPoster():
    def __init__(self, args, auth):
        auth_api : tweepy.OAuth1UserHandler = tweepy.OAuth1UserHandler(
            auth['api_key'], auth['api_key_secret'], auth['access_token'], auth['access_token_secret']
        )
        self.client : tweepy.Client = tweepy.Client(
            consumer_key=auth['api_key'],
            consumer_secret=auth['api_key_secret'],
            access_token=auth['access_token'],
            access_token_secret=auth['access_token_secret']
        )
        self.api = tweepy.API(auth_api)

    def make_post(self, text=None, file=None):
        try:
            id_pic = None
            if file is not None:
                id_pic = [self.api.media_upload(file).media_id]
            return str(self.client.create_tweet(text=text, media_ids=id_pic))
        except Exception as e:
            print(e)
            return 500
        
def twitter(pipeline: MyPipeline=None, args: dict=None):
    # check if there is a field 'twitter' and 'auth' in the args
    print("auth" not in args.keys(), "twitter" not in args['auth'])
    if "auth" not in args.keys() or "twitter" not in args['auth']:
        pipeline.log("Twitter not in args")
        return False
    auth = args['auth']['twitter']
    account = TwitterPoster(None, auth)
    twitter_return = account.make_post(text=args['string'], file=args['media'])
    pipeline.log("Twitter return: " + str(twitter_return))
    return args
