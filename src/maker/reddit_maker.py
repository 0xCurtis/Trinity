import json
import requests
from src.pipeline import MyPipeline
from bs4 import BeautifulSoup as bs
import sys, os

user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
cookie = 'edgebucket=FacFxnERBsR8z1sGSH; csv=2; __stripe_mid=e74f878c-bb67-47ed-a064-0f5ce4668d3eb7118e; pc=3q; recent_srs=t5_2r4yl%2Ct5_5yggun%2Ct5_6u067o%2Ct5_2ub9j%2Ct5_2s96i%2Ct5_3273w%2Ct5_2uwys%2Ct5_32sxp%2Ct5_2qhta%2C; theme=1; eu_cookie={%22opted%22:true%2C%22nonessential%22:true}; t2_vish2xyo_recentclicks3=t3_tt7a1a%2Ct3_1ce8d9d; __stripe_sid=fd08d9ce-0103-4352-b7e4-83a933e6b5a0b44f42; g_state={"i_l":0}; reddit_session=100340249645120%2C2024-05-03T03%3A54%3A00%2C91a546485e0ce3a4e767de5350a9a8144032e88f; loid=000000000zkfo9xhkw.2.1714708439365.Z0FBQUFBQm1ORl9ZTHcxSTZ1Mi1QLW9PNzd4Q2MwT2VaT2pacGxGSl9QQnlJNXV5R2R4QVZnNzZDRzM0YVJzMHhpOHdtVncxcjgxNWZLbm9sTDBxeFJ6OEdQa08xRW5lbzN2TnBVbzE1VWk4YjZpcEJfak45WUt0ZWxaNFF6TWxPRVE5WDBpd2Zvck8; token_v2=eyJhbGciOiJSUzI1NiIsImtpZCI6IlNIQTI1NjpzS3dsMnlsV0VtMjVmcXhwTU40cWY4MXE2OWFFdWFyMnpLMUdhVGxjdWNZIiwidHlwIjoiSldUIn0.eyJzdWIiOiJ1c2VyIiwiZXhwIjoxNzE0Nzk0ODQwLjMxMjMzMywiaWF0IjoxNzE0NzA4NDQwLjMxMjMzMywianRpIjoiMTZYb1huS0gtLU1JWlVKOHJkb3RvVUNlbDA4d0N3IiwiY2lkIjoiMFItV0FNaHVvby1NeVEiLCJsaWQiOiJ0Ml96a2ZvOXhoa3ciLCJhaWQiOiJ0Ml96a2ZvOXhoa3ciLCJsY2EiOjE3MTQ3MDg0MzkzNjUsInNjcCI6ImVKeGtrZEdPdERBSWhkLWwxejdCX3lwX05odHNjWWFzTFFhb2szbjdEVm9jazcwN2NMNGlIUDhuS0lxRkxFMnVCS0drS1dFRld0T1VOaUx2NTh5OU9aRUZTeUZUUjg0M3l3b2thVXBQVW1ONXB5bFJ3V1prTGxmYXNVS0RCNllwVlM2WjIwS1BTNXZRM0kxRnowNk1xbHhXSHRUWW8zSnBiR01LMnhQanpjWnFReXF1eTZsTVlGa29uOFdMZnZ5Ry10WS1mN2JmaEhZd3JLZ0tEX1RPdUZ4d1lfSERGSGJfbnByMGJGMndxTDNYZzlRLTEtTjI3Yk5tb2RtNV9WelB2emFTY1RtRzVpZll2N3QtQ1IxNDVIbVpVUWN3WWcwX3lyQWo2X0N2T29ES0JRV01KWWhQSTVBcmwyX19KZGl1VGY4YXR5ZC0tR2JFVFdfNHJSbW81eExFb1VfajZ6Y0FBUF9fWERfZTR3IiwicmNpZCI6IjRCVm8ycGcyTl9YWl92TVkyX2l6TVM1bGpnNEFZMjZDa2I4YUNDbF96QWciLCJmbG8iOjJ9.lrxdNjV1SXaNYE6twQTYvQxbKe1Fi-pOldTrTGK2ICfHks1ksAxJBiP_91Hyvmrwo-1TKwxMIoWvaBi25iPlRs13lUXxolDveWIt1_FfbWo95Hzme2wfG4L7urWEwHvB3Pd3uG2kvD45bKohg-PYZBO1vPG-xCD9HrxUzVhgLw1kWHC-Q_aSWGgrx8xXJcohnU7DGbcK6ZVRQsjIe4wofMQS0cjRPzyzoRjZHOkEVwMT-fa-3yIatkePxLzAxC7ICleXwsC1F9Upg1WkhWexAqGOPkc6r9lDuV6ARZ8MyuiVd8Qi4JzfqRmeSv4Ru6vR9rp9ZCZBelCJ_oV1t5rRzQ; csrf_token=34196c71d95b60bd5be28d6430e2cdf3; session_tracker=ijnafjaolbbploagic.0.1714708498323.Z0FBQUFBQm1OR0FTSHozN2NoalJyTUg0TWZCVHVPTXdKaFhoS1lqajBoVDl4c0NKYzJVMXBaYkFpNldwbXpPbldWR1UxeWI0WUN0Y0JBMHl3UDdDMzJfUXZlczJ1ZU0tRjBEa213aEFORjlmNkswUFR3c19NajZWa2JYRmlzWTF5aHkySmpKY0N2RzY'

def get_reddit_feed(subreddit: str):
    res = requests.get('https://www.reddit.com/r/' + subreddit + '/.json', headers={'User-Agent': user_agent, 'cookie': cookie})
    return res.json()

def get_num_post(feed, count):
    # check if a key exist in the dict
    try:
        if 'url_overridden_by_dest' in feed['data']['children'][count]['data']:
            return feed['data']['children'][count]['data']['url_overridden_by_dest']
    except:  
        return None
    return None

def reddit(pipeline : MyPipeline, args: dict = None):
    print("IN REDDIT")
    count = 0
    feed = get_reddit_feed(args['reddit']['subreddit'])
    print("FEED SCRAPED")
    content_link = get_num_post(feed, count)
    try:
        while content_link is None or (args["unique_posts"] and pipeline.check_post_history(content_link)):
            print("IN WHILE")
            count += 1
            content_link = get_num_post(feed, count)
        # if the post is a gallery, get the first image
        print("OUT WHILE")
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
        print("OUT REDDIT")
        return args
    except Exception as e:
        print("Exception: ", e)
        # also log the line where the error occurred
        pipeline.log("Pipeline execution failed: " + str(e))
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        pipeline.log(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")
        pipeline.add_to_post_history(content_link)
        raise(e)

if __name__ == '__main__':
    print(get_reddit_feed('lanadelrey'))