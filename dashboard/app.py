import json
import os
import requests
from pathlib import Path
from flask import Flask, jsonify, render_template, request
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
            public_link = (
                f"https://t.me/{username}" if username else chat.get("invite_link")
            )
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
            get_telegram_api_url("getChatMemberCount"),
            params={"chat_id": chat_id},
            timeout=10,
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


@app.route("/api/stats")
def api_stats():
    pipelines = load_pipelines()
    chat_ids = get_unique_chat_ids(pipelines)

    total_pipelines = len(pipelines)
    enabled_pipelines = sum(1 for p in pipelines if p.get("enabled", False))
    disabled_pipelines = total_pipelines - enabled_pipelines
    total_channels = len(chat_ids)

    channel_stats = []
    for chat_id in chat_ids:
        info = get_chat_info(chat_id)
        if info.get("id"):
            info["member_count"] = get_member_count(chat_id)
            channel_stats.append(info)

    total_members = sum(ch.get("member_count", 0) or 0 for ch in channel_stats)
    public_channels = sum(1 for ch in channel_stats if ch.get("is_public", False))

    return jsonify(
        {
            "total_pipelines": total_pipelines,
            "enabled_pipelines": enabled_pipelines,
            "disabled_pipelines": disabled_pipelines,
            "total_channels": total_channels,
            "total_members": total_members,
            "public_channels": public_channels,
            "private_channels": total_channels - public_channels,
        }
    )


@app.route("/api/history")
def api_history():
    LOGS_DIR = BASE_DIR / "bot" / "logs"
    pipelines = load_pipelines()

    history = []
    for p in pipelines:
        pipeline_name = p.get("name", "unknown")
        log_file = LOGS_DIR / f"{pipeline_name}.log"

        runs = []
        if log_file.exists():
            try:
                with open(log_file, encoding="utf-8") as f:
                    lines = f.readlines()
                    for line in lines:
                        line = line.strip()
                        if "created at" in line:
                            timestamp = (
                                line.split("created at ")[-1][:19]
                                if "created at " in line
                                else ""
                            )
                            runs.append(
                                {
                                    "type": "created",
                                    "timestamp": timestamp,
                                    "message": line,
                                }
                            )
                        elif "Pipeline executed successfully" in line:
                            timestamp = line.split(" : ")[0] if " : " in line else ""
                            runs.append(
                                {
                                    "type": "success",
                                    "timestamp": timestamp,
                                    "message": "Executed successfully",
                                }
                            )
                        elif "error" in line.lower() or "failed" in line.lower():
                            timestamp = line.split(" : ")[0] if " : " in line else ""
                            runs.append(
                                {
                                    "type": "error",
                                    "timestamp": timestamp,
                                    "message": line[:200],
                                }
                            )
            except Exception:
                pass

        history.append({"pipeline": pipeline_name, "runs": runs[-10:] if runs else []})

    return jsonify(history)


@app.route("/api/logs")
def api_logs():
    LOGS_DIR = BASE_DIR / "bot" / "logs"
    pipelines = load_pipelines()

    logs = []
    for p in pipelines:
        pipeline_name = p.get("name", "unknown")
        log_file = LOGS_DIR / f"{pipeline_name}.log"

        if log_file.exists():
            try:
                with open(log_file, encoding="utf-8") as f:
                    lines = f.readlines()
                    recent_lines = lines[-50:] if len(lines) > 50 else lines
                    logs.append(
                        {
                            "pipeline": pipeline_name,
                            "lines": [line.strip() for line in recent_lines],
                        }
                    )
            except Exception:
                logs.append({"pipeline": pipeline_name, "lines": ["Error reading log"]})

    return jsonify(logs)


def validate_pipeline(pipeline: dict) -> tuple[bool, str]:
    """Validate pipeline configuration."""
    if not pipeline.get("name"):
        return False, "Pipeline name is required"

    name = pipeline["name"]
    if not name.replace("_", "").isalnum():
        return False, "Pipeline name must be alphanumeric with underscores only"

    if not pipeline.get("source", {}).get("task"):
        return False, "source.task is required"

    if not pipeline.get("post", {}).get("task"):
        return False, "post.task is required"

    interval = pipeline.get("run_every_minutes")
    if interval is not None:
        try:
            interval = int(interval)
            if interval <= 0:
                return False, "run_every_minutes must be a positive integer"
        except (ValueError, TypeError):
            return False, "run_every_minutes must be a valid integer"

    return True, ""


def create_backup(pipeline_name: str) -> bool:
    """Create a backup of a pipeline before editing."""
    pipeline_file = PIPELINES_DIR / f"{pipeline_name}.json"
    if not pipeline_file.exists():
        return False

    backups_dir = PIPELINES_DIR / ".backups"
    backups_dir.mkdir(exist_ok=True)

    import time

    backup_file = backups_dir / f"{pipeline_name}_{int(time.time())}.json"

    try:
        with open(pipeline_file, encoding="utf-8") as src:
            with open(backup_file, "w", encoding="utf-8") as dst:
                dst.write(src.read())

        backups = sorted(backups_dir.glob(f"{pipeline_name}_*.json"))
        while len(backups) > 3:
            backups[0].unlink()
            backups.pop(0)

        return True
    except Exception:
        return False


@app.route("/api/templates")
def api_templates():
    """Get available pipeline templates."""
    templates_file = Path(__file__).parent / "templates" / "pipeline_templates.json"
    if templates_file.exists():
        with open(templates_file, encoding="utf-8") as f:
            return jsonify(json.load(f))
    return jsonify({})


@app.route("/api/pipelines/<name>", methods=["GET"])
def api_pipeline_get(name):
    """Get a specific pipeline."""
    pipeline_file = PIPELINES_DIR / f"{name}.json"
    if not pipeline_file.exists():
        return jsonify({"error": "Pipeline not found"}), 404

    try:
        with open(pipeline_file, encoding="utf-8") as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pipelines", methods=["POST"])
def api_pipeline_create():
    """Create a new pipeline."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Pipeline name is required"}), 400

    pipeline_file = PIPELINES_DIR / f"{name}.json"
    if pipeline_file.exists():
        return jsonify({"error": "Pipeline already exists"}), 400

    valid, error = validate_pipeline(data)
    if not valid:
        return jsonify({"error": error}), 400

    try:
        with open(pipeline_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return jsonify({"success": True, "pipeline": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pipelines/<name>", methods=["PUT"])
def api_pipeline_update(name):
    """Update an existing pipeline."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    pipeline_file = PIPELINES_DIR / f"{name}.json"
    if not pipeline_file.exists():
        return jsonify({"error": "Pipeline not found"}), 404

    create_backup(name)

    valid, error = validate_pipeline(data)
    if not valid:
        return jsonify({"error": error}), 400

    try:
        with open(pipeline_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return jsonify({"success": True, "pipeline": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pipelines/<name>", methods=["DELETE"])
def api_pipeline_delete(name):
    """Delete a pipeline."""
    pipeline_file = PIPELINES_DIR / f"{name}.json"
    if not pipeline_file.exists():
        return jsonify({"error": "Pipeline not found"}), 404

    create_backup(name)

    try:
        pipeline_file.unlink()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pipelines/backup/<name>", methods=["GET"])
def api_pipeline_backups(name):
    """Get available backups for a pipeline."""
    backups_dir = PIPELINES_DIR / ".backups"
    backups = []

    if backups_dir.exists():
        for f in sorted(backups_dir.glob(f"{name}_*.json"), reverse=True):
            backups.append({"name": f.name, "timestamp": f.stat().st_mtime})

    return jsonify(backups)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
