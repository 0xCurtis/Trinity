import json
import os

import requests

from src.pipeline import MyPipeline
from src.retry import retry_with_backoff


@retry_with_backoff(max_retries=3, base_delay=2.0)
def send_media(
    bot_token, chat_id, file_path, media_type, buttons: list[dict] = None, text: str = None
):
    """
    Send a media message to a Telegram chat using a local file.

    :param buttons: list[dict] - List of buttons to be sent with the message
    :param bot_token: str - Telegram bot token
    :param chat_id: str - Telegram chat ID
    :param file_path: str - Path to the local file
    :param media_type: str - Type of the media ('photo', 'video', 'animation', 'document')
    """
    send_functions = {
        "photo": "sendPhoto",
        "video": "sendVideo",
        "animation": "sendAnimation",
        "document": "sendDocument",
    }

    method = send_functions.get(media_type)

    if not method:
        raise ValueError("Unsupported media type")

    url = f"https://api.telegram.org/bot{bot_token}/{method}"
    reply_markup = json.dumps({"inline_keyboard": buttons or []})

    try:
        return _send_file(bot_token, chat_id, file_path, media_type, method, reply_markup, text)
    except RuntimeError as e:
        error_msg = str(e)
        if "file too large" in error_msg.lower() or "payload too large" in error_msg.lower():
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            print(f"File too large ({file_size:.1f}MB), trying fallback...")
            return _send_as_document_fallback(bot_token, chat_id, file_path, reply_markup, text)
        raise


def _send_file(bot_token, chat_id, file_path, media_type, method, reply_markup, text):
    url = f"https://api.telegram.org/bot{bot_token}/{method}"
    with open(file_path, "rb") as f:
        files = {media_type: f}
        data = {"chat_id": chat_id, "reply_markup": reply_markup, "caption": text or ""}
        response = requests.post(url, files=files, data=data)

    res = response.json()
    if not res.get("ok"):
        err = res.get("description", res)
        code = res.get("error_code", "")
        raise RuntimeError(f"Telegram API error {code}: {err}")
    return res


def _send_as_document_fallback(bot_token, chat_id, file_path, reply_markup, text):
    """Fallback: send large files as document."""
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"

    file_name = os.path.basename(file_path)

    with open(file_path, "rb") as f:
        files = {"document": (file_name, f)}
        data = {"chat_id": chat_id, "reply_markup": reply_markup, "caption": text or ""}
        response = requests.post(url, files=files, data=data)

    res = response.json()
    if not res.get("ok"):
        err = res.get("description", res)
        code = res.get("error_code", "")
        raise RuntimeError(f"Telegram API error (document fallback) {code}: {err}")
    return res


@retry_with_backoff(max_retries=3, base_delay=2.0)
def send_message_request(
    bot_token: str, chat_id: str, text: str, buttons: list[dict] = None
) -> dict:
    """Send a text message to a Telegram chat."""
    reply_markup = json.dumps({"inline_keyboard": buttons or []})
    data = {"chat_id": chat_id, "reply_markup": reply_markup, "text": text}
    resp = requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", data=data)
    res = resp.json()
    if not res.get("ok"):
        err = res.get("description", res)
        code = res.get("error_code", "")
        raise RuntimeError(f"Telegram API error {code}: {err}")
    return res


def telegram(pipeline: MyPipeline = None, args: dict = None):
    chat_id = args["telegram"]["chat_id"]
    token = args["auth"]["telegram"]["token"]
    buttons = args["telegram"].get("buttons", None)
    media = args.get("media", None)
    if media:
        res = send_media(
            token, chat_id, media[0]["path"], media[0]["type"], buttons, args["string"]
        )
        pipeline.log(f"telegram response: {res}")
    else:
        res = send_message_request(token, chat_id, args["string"], buttons)
        pipeline.log(f"telegram response: {res}")

    return args
