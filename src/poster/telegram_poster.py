import requests
from src.pipeline import MyPipeline
import json


def send_media(bot_token, chat_id, file_path, media_type, buttons: list[dict] = None, text: str = None):
    """
    Send a media message to a Telegram chat using a local file.

    :param buttons: list[dict] - List of buttons to be sent with the message
    :param bot_token: str - Telegram bot token
    :param chat_id: str - Telegram chat ID
    :param file_path: str - Path to the local file
    :param media_type: str - Type of the media ('photo', 'video', 'animation', 'document')
    """
    send_functions = {
        'photo': 'sendPhoto',
        'video': 'sendVideo',
        'animation': 'sendAnimation',
        'document': 'sendDocument'
    }

    method = send_functions.get(media_type)

    if not method:
        raise ValueError("Unsupported media type")

    url = f"https://api.telegram.org/bot{bot_token}/{method}"
    reply_markup = json.dumps({'inline_keyboard': buttons})
    files = {media_type: open(file_path, 'rb')}
    data = {"chat_id": chat_id, "reply_markup": reply_markup, "caption": text or ""}

    response = requests.post(url, files=files, data=data)
    files[media_type].close()  # It's important to close the file handle after the request is made

    return response.json()


def telegram(pipeline: MyPipeline = None, args: dict = None):
    chat_id = args["telegram"]["chat_id"]
    token = args["auth"]["telegram"]["token"]
    # check if there are any buttons in args/telegram/buttons
    buttons = args["telegram"].get("buttons", None)
    # check if there is any file to send
    media = args.get("media", None)
    if media:
        res = send_media(token, chat_id, media[0]["path"], media[0]["type"], buttons, args["string"])
        pipeline.log(f"telegram response: {res}")
    else:
        reply_markup = json.dumps({'inline_keyboard': buttons})
        data = {"chat_id": chat_id, "reply_markup": reply_markup, "text": args["string"]}
        res = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data=data)
        pipeline.log(f"telegram response: {res.json()}")
    # add file names to the history
    
    return args