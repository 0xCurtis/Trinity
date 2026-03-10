import json
import os
import requests
from pathlib import Path
from flask import Flask, jsonify, render_template
from dotenv import load_dotenv

app = Flask(__name__)

BASE_DIR = Path(__file__).parent.parent
PIPELINES_DIR = BASE_DIR / "bot" / "pipelines"

load_dotenv(Path(__file__).parent / ".env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")


def get_telegram_api_url(method):
    return f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"


def get_chat_info(chat_id):
    if not TELEGRAM_BOT_TOKEN:
        return {"error": "Bot token not configured"}

    try:
        response = requests.get(
            get_telegram_api_url("getChat"), params={"chat_id": chat_id}, timeout=10
        )
        data = response.json()
        if data.get("ok"):
            chat = data.get("result", {})
            username = chat.get("username")
            is_public = bool(username)
            public_link = f"https://t.me/{username}" if username else chat.get("invite_link")
            return {
                "id": chat.get("id"),
                "title": chat.get("title", "Unknown"),
                "username": username,
                "type": chat.get("type"),
                "description": chat.get("description", ""),
                "invite_link": public_link,
                "is_public": is_public,
                "member_count": None,
            }
        return {"error": data.get("description", "Unknown error")}
    except Exception as e:
        return {"error": str(e)}


def get_member_count(chat_id):
    if not TELEGRAM_BOT_TOKEN:
        return None

    try:
        response = requests.get(
            get_telegram_api_url("getChatMemberCount"), params={"chat_id": chat_id}, timeout=10
        )
        data = response.json()
        if data.get("ok"):
            return data.get("result")
    except:
        pass
    return None


def load_pipelines():
    pipelines = []
    if PIPELINES_DIR.exists():
        for file in PIPELINES_DIR.glob("*.json"):
            try:
                with open(file, encoding="utf-8") as f:
                    config = json.load(f)
                    pipelines.append(config)
            except Exception:
                pass
    return pipelines


def get_unique_chat_ids(pipelines):
    chat_ids = set()
    for p in pipelines:
        chat_id = p.get("telegram", {}).get("chat_id")
        if chat_id:
            chat_ids.add(chat_id)
    return chat_ids


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/channels")
def api_channels():
    pipelines = load_pipelines()
    chat_ids = get_unique_chat_ids(pipelines)

    channels = []
    for chat_id in chat_ids:
        info = get_chat_info(chat_id)
        if info.get("id"):
            info["member_count"] = get_member_count(chat_id)
            channels.append(info)

    return jsonify(channels)


@app.route("/api/pipelines")
def api_pipelines():
    pipelines = load_pipelines()

    result = []
    for p in pipelines:
        chat_id = p.get("telegram", {}).get("chat_id", "")
        result.append(
            {
                "name": p.get("name", "Unknown"),
                "enabled": p.get("enabled", False),
                "description": p.get("description", ""),
                "source": p.get("source", {}),
                "target_channel": chat_id,
                "run_every_minutes": p.get("run_every_minutes"),
            }
        )

    return jsonify(result)


@app.route("/api/summary")
def api_summary():
    pipelines = load_pipelines()
    chat_ids = get_unique_chat_ids(pipelines)

    channel_to_pipelines = {cid: [] for cid in chat_ids}

    for p in pipelines:
        chat_id = p.get("telegram", {}).get("chat_id")
        if chat_id and chat_id in channel_to_pipelines:
            channel_to_pipelines[chat_id].append(p.get("name", "Unknown"))

    summary = []
    for chat_id in chat_ids:
        info = get_chat_info(chat_id)
        if info.get("id"):
            info["member_count"] = get_member_count(chat_id)
            info["pipelines"] = channel_to_pipelines[chat_id]
            summary.append(info)

    return jsonify(summary)


@app.route("/api/health")
def api_health():
    return jsonify(
        {
            "status": "ok",
            "token_configured": bool(TELEGRAM_BOT_TOKEN),
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
