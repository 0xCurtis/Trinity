import os
import sys

import requests
from bs4 import BeautifulSoup as bs

from src.retry import retry_with_backoff


@retry_with_backoff(max_retries=3, base_delay=2.0)
def get_reddit_feed(subreddit: str):
    return requests.get("https://www.reddit.com/r/" + subreddit + "/.json").json()


def get_num_post(feed, count):
    try:
        if "url_overridden_by_dest" in feed["data"]["children"][count]["data"]:
            return feed["data"]["children"][count]["data"]["url_overridden_by_dest"]
    except (KeyError, IndexError, TypeError):
        return None
    return None


def reddit(pipeline, args: dict = None):
    count = 0
    feed = get_reddit_feed(args["reddit"]["subreddit"])
    content_link = get_num_post(feed, count)
    print(content_link)
    try:
        while content_link is None or (
            args["unique_posts"] and pipeline.check_post_history(content_link)
        ):
            count += 1
            content_link = get_num_post(feed, count)

        content_name = None
        if "gallery" in content_link:
            content_gallery = requests.get(content_link)
            soup = bs(content_gallery.content, "html.parser")
            images = soup.find_all("img", src=True)
            for img in images:
                if img["src"].startswith("https://preview.redd.it/"):
                    img_url = img["src"]
                    content_name = img_url.split("/")[-1].split("?")[0]
                    with open(content_name, "wb") as f:
                        f.write(requests.get(img_url).content)
                    break
        else:
            content = requests.get(content_link)
            content_name = content_link.split("/")[-1]
            with open(content_name, "wb") as f:
                f.write(content.content)

        if content_name is None:
            raise ValueError("Failed to extract content filename")

        if content_name.split(".")[-1] in ["jpg", "jpeg", "png"]:
            content_type = "photo"
        elif content_name.split(".")[-1] in ["gif"]:
            content_type = "animation"
        else:
            content_type = "video"

        pipeline.add_media(content_type, content_name)
        args.setdefault("_add_to_history", []).append(content_link)
        args["string"] = feed["data"]["children"][count]["data"]["title"]
        return args
    except Exception as e:
        pipeline.log("Pipeline execution failed: " + str(e))
        exc_type, exc_obj, exc_tb = sys.exc_info()
        if exc_tb:
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            pipeline.log(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")
        raise
