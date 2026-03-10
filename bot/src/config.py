import json
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

APP_DIR = Path(__file__).parent


def load_env() -> None:
    """Load environment variables from .env file."""
    env_path = APP_DIR / ".env"
    if env_path.exists():
        load_dotenv(env_path)


def get_env(key: str, default: str | None = None) -> str | None:
    """Get environment variable value."""
    return os.environ.get(key, default)


def get_env_required(key: str) -> str:
    """Get required environment variable, raises if not found."""
    value = os.environ.get(key)
    if value is None:
        raise ValueError(f"Required environment variable {key} is not set")
    return value


def resolve_secrets(obj: Any) -> Any:
    """Recursively resolve ${ENV_VAR} placeholders in config objects."""
    if isinstance(obj, dict):
        return {k: resolve_secrets(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [resolve_secrets(item) for item in obj]
    elif isinstance(obj, str):
        return _resolve_string(obj)
    return obj


def _resolve_string(value: str) -> str:
    """Resolve ${VAR} patterns in a string."""
    pattern = r"\$\{([^}]+)\}"

    def replacer(match):
        var_name = match.group(1)
        env_value = os.environ.get(var_name)
        if env_value is None:
            raise ValueError(f"Environment variable {var_name} referenced in config is not set")
        return env_value

    return re.sub(pattern, replacer, value)


def load_pipeline_config(file_path: Path) -> dict:
    """Load a pipeline JSON config and resolve secrets."""
    with open(file_path, encoding="utf-8") as f:
        config = json.load(f)
    return resolve_secrets(config)


load_env()
