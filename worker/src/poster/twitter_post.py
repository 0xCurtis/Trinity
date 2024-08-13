import sys
import tweepy
#from src.pipeline import MyPipeline

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
            print(file)
            if file is not None:
                id_pic = []
                for f in file:
                    print("before upload")
                    id_media = self.api.media_upload(f['path'])
                    print("after upload")
                    print(id_media)
                    id_pic.append(self.api.media_upload(f['path']).media_id)
            res = self.client.create_tweet(text=text, media_ids=id_pic)
            return res
        except Exception as e:
            print(e)
            return 500
        
def twitter(pipeline=None, args: dict=None):
    # check if there is a field 'twitter' and 'auth' in the args
    if "auth" not in args.keys() or "twitter" not in args['auth']:
        pipeline.log("Twitter not in args")
        return False
    auth = args['auth']['twitter']
    account = TwitterPoster(None, auth)
    media = args['media'] if 'media' in args else None
    print(media)
    twitter_return = account.make_post(text=args['string'], file=media)
    return args


if __name__ == "__main__":
    args = {
        "auth": {
                "twitter": {
                    "access_token": "1607229586353410048-1whNcj7SEdsZmoVfMu4e9JpvSoAXQ3",
                    "access_token_secret": "p3bhBvuGvxtQdb0276VKRBfB3xxkVarhBNuSb4QKxUthB",
                    "api_key": "tHUjjSsHEU0OBZngXlc8oj7Jo",
                    "api_key_secret": "dKFFspNmtKSwI7GvJaxD3aZjfTT9F60OgO2H6HPt05e4LqYeTk"
                },
        },
        "string": "Hello World",
    }
    twitter(None, args)