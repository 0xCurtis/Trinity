import requests
import os
from src.pipeline import MyPipeline

"""
No auth required /

unique integration

args required :
    tags : str
    sort : str
"""


def get_auth_token():
    base_url = "https://api.redgifs.com/v2/auth/temporary"
    res = requests.get(base_url, headers={"content-type": "application/x-www-form-urlencoded"})
    res_json = res.json()
    return res_json['token']

def check_token():
    script_path = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_path)
    file_path = os.path.join(script_dir, "red_gifs.token")
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            f.write(get_auth_token())
    with open(file_path, 'r') as f:
        token = f.read()
    headers = {
        "Authorization": f"Bearer {token}",
    }
    # make a dummy request to test the token
    if requests.get("https://api.redgifs.com/v2/gifs/search?order=best&count=40&page=1", headers=headers).status_code != 200:
        token = get_auth_token()
        headers = {
        "Authorization": f"Bearer {token}",
        }
        # clean red_gifs.token and write the new token
        with open(file_path, 'w') as f:
            f.write(token)
    return headers

def redgifs(pipeline : MyPipeline = None, args : dict = None) -> dict:
    headers = check_token()
    base_url = f"https://api.redgifs.com/v2/gifs/search?order={args['redgifs']['sort']}&count=40&page=1&type=g&search_text={args['redgifs']['tags']}"
    res = requests.get(base_url, headers=headers)
    url = res.json()
    count = 0
    download_link = url['gifs'][count]['urls']['hd']
    filename = download_link.split('/')[-1].split('?')[0]
    while url['gifs'][count]['urls']['hd'] is None or (args["unique_posts"] and pipeline.check_post_history(filename)):
        count += 1
        download_link = url['gifs'][count]['urls']['hd']
        filename = download_link.split('/')[-1].split('?')[0]
    with open(filename, 'wb') as f:
        f.write(requests.get(download_link).content)
    pipeline.add_media("video", filename)
    pipeline.add_to_post_history(filename)
    return args

if __name__ == "__main__":
    test_dict = {
        "type": "video",
        "tags": "women",
    }
    redgifs(test_dict) 
