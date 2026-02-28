import os
import sys
from pathlib import Path
from threading import Lock

from flask import Flask, jsonify

APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(APP_DIR / "src"))

app = Flask(__name__)

_status_lock = Lock()
_last_run_status = {"status": "unknown", "pipelines": {}, "last_error": None}
_start_time = None


def set_status(status: str, pipelines: dict = None, error: str = None):
    """Update the current status."""
    global _last_run_status
    with _status_lock:
        _last_run_status["status"] = status
        if pipelines is not None:
            _last_run_status["pipelines"] = pipelines
        if error is not None:
            _last_run_status["last_error"] = error


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})


@app.route("/status")
def status():
    """Get pipeline status."""
    with _status_lock:
        return jsonify(
            {
                "status": _last_run_status["status"],
                "pipelines": _last_run_status["pipelines"],
                "last_error": _last_run_status["last_error"],
                "uptime_seconds": (os.times().elapsed - _start_time) if _start_time else 0,
            }
        )


def run_server(port: int = 5000):
    """Run the health check server."""
    global _start_time
    _start_time = os.times().elapsed
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    run_server()
