import requests


class TelegramNotifier:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"

    def send(self, text: str, parse_mode: str = "Markdown") -> dict:
        url = f"{self.base_url}/sendMessage"
        data = {"chat_id": self.chat_id, "text": text, "parse_mode": parse_mode}
        response = requests.post(url, data=data)
        return response.json()


def send_error_notification(
    token: str,
    chat_id: str,
    pipeline_name: str,
    description: str,
    error_message: str,
    failed_task: str,
    timestamp: str,
):
    if not token or not chat_id:
        return {"ok": False, "error": "Missing token or chat_id"}

    notifier = TelegramNotifier(token, chat_id)

    message = f"""🔴 *Pipeline Failed*

*Name:* `{pipeline_name}`
*Description:* {description}
*Time:* {timestamp}
*Failed Task:* `{failed_task}`
*Error:* {error_message[:200]}"""

    return notifier.send(message)


def send_success_notification(
    token: str,
    chat_id: str,
    pipeline_name: str,
    description: str,
    timestamp: str,
):
    if not token or not chat_id:
        return {"ok": False, "error": "Missing token or chat_id"}

    notifier = TelegramNotifier(token, chat_id)

    message = f"""✅ *Pipeline Succeeded*

*Name:* `{pipeline_name}`
*Description:* {description}
*Time:* {timestamp}"""

    return notifier.send(message)
