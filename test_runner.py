import os

import requests

token = os.environ.get("TELEGRAM_BOT_TOKEN")
chat_id = os.environ.get("TELEGRAM_CHAT_ID")

if not token or not chat_id:
    print("Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables must be set")
    exit(1)

data = {"chat_id": chat_id, "text": "test send"}
res = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data=data)
print(res.json())
