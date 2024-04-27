import json
import requests
#from src.pipeline import MyPipeline
from bs4 import BeautifulSoup as bs
import sys, os

def get_reddit_feed(subreddit: str):
    return requests.get('https://www.reddit.com/r/' + subreddit + '/.json').json()

def get_num_post(feed, count):
    # check if a key exist in the dict
    try:
        if 'url_overridden_by_dest' in feed['data']['children'][count]['data']:
            return feed['data']['children'][count]['data']['url_overridden_by_dest']
    except:  
        return None
    return None

def reddit(pipeline, args: dict = None):
    count = 0
    feed = get_reddit_feed(args['reddit']['subreddit'])
    content_link = get_num_post(feed, count)
    print(content_link)
    try:
        while content_link is None or (args["unique_posts"] and pipeline.check_post_history(content_link)):
            count += 1
            content_link = get_num_post(feed, count)
        # if the post is a gallery, get the first image
        if 'gallery' in content_link:
            content_gallery = requests.get(content_link)
            soup = bs(content_gallery.content, 'html.parser')
            images = soup.find_all('img', src=True)
            for img in images:
                if img['src'].startswith('https://preview.redd.it/'):
                    requests.get(img['src'])
                    content_name = img['src'].split('/')[-1].split('?')[0]
                    with open(content_name, 'wb') as f:
                        f.write(requests.get(img['src']).content)
                    break
        else:
            content = requests.get(content_link)
            content_name = content_link.split('/')[-1]
            with open(content_name, 'wb') as f:
                f.write(content.content)

        if content_name.split('.')[-1] in ['jpg', 'jpeg', 'png']:
            content_type = "photo"
        elif content_name.split('.')[-1] in ['gif']:
            content_type = "animation"
        else:
            content_type = "video"

        pipeline.add_media(content_type, content_name)
        pipeline.add_to_post_history(content_link)
        args['string'] = feed['data']['children'][count]['data']['title']
        return args
    except Exception as e:
        # also log the line where the error occurred
        pipeline.log("Pipeline execution failed: " + str(e))
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        pipeline.log(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")
        pipeline.add_to_post_history(content_link)
        raise(e)
