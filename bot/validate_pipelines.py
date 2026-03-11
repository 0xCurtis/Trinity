#!/usr/bin/env python3
"""
Pipeline configuration validator.
Checks all pipelines for required parameters in makers, posters, and middlewares.
"""

import json
import sys
from pathlib import Path


REQUIRED_BY_MAKER = {
    "src.maker.redgifs_maker.redgifs": ["source.redgifs"],
    "src.maker.reddit_maker.reddit": ["source.reddit"],
    "src.maker.string_maker.string": ["source.string"],
}

REQUIRED_BY_POSTER = {
    "src.poster.telegram_poster.telegram": ["telegram.chat_id", "auth.telegram.token"],
    "src.poster.twitter_post.twitter": ["auth.twitter"],
    "src.poster.console_poster.console": [],
}

REQUIRED_BY_MIDDLEWARE = {
    "src.middleware.watermark.watermark": [],
    "src.middleware.fake_delay.fake_delay": [],
}


def load_pipelines(pipelines_dir: Path):
    """Load all pipeline configs from directory."""
    pipelines = []
    if not pipelines_dir.exists():
        print(f"Error: Pipelines directory not found: {pipelines_dir}")
        return pipelines

    for file in pipelines_dir.glob("*.json"):
        if file.stem == "global":
            continue
        try:
            with open(file, encoding="utf-8") as f:
                config = json.load(f)
                config["_file"] = file.stem
                pipelines.append(config)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {file.name}: {e}")
        except Exception as e:
            print(f"Error loading {file.name}: {e}")

    return pipelines


def get_nested_value(data: dict, path: str):
    """Get value from nested dict using dot notation."""
    keys = path.split(".")
    value = data
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return None
    return value


def check_required(data: dict, required_paths: list, component: str, errors: list):
    """Check if required paths exist in data."""
    for path in required_paths:
        value = get_nested_value(data, path)
        if value is None or value == "":
            errors.append(f"  Missing required: {path} for {component}")


def validate_pipeline(pipeline: dict) -> list:
    """Validate a single pipeline configuration."""
    errors = []
    name = pipeline.get("name", pipeline.get("_file", "unknown"))

    source_task = get_nested_value(pipeline, "source.task")
    post_task = get_nested_value(pipeline, "post.task")
    middlewares = pipeline.get("middleware", [])

    if not source_task:
        errors.append(f"Missing required: source.task")
    else:
        required = REQUIRED_BY_MAKER.get(source_task, [])
        check_required(pipeline, required, f"maker ({source_task})", errors)

    if not post_task:
        errors.append(f"Missing required: post.task")
    else:
        required = REQUIRED_BY_POSTER.get(post_task, [])
        check_required(pipeline, required, f"poster ({post_task})", errors)

    for mw in middlewares:
        required = REQUIRED_BY_MIDDLEWARE.get(mw, [])
        if mw == "src.middleware.watermark.watermark":
            wm_config = pipeline.get("watermark", {})
            if wm_config:
                wm_type = wm_config.get("type", "image")
                if wm_type == "image":
                    if not wm_config.get("image_path"):
                        errors.append("  Missing required: watermark.image_path")
                if wm_type == "text":
                    if not wm_config.get("text"):
                        errors.append("  Missing required: watermark.text")
        check_required(pipeline, required, f"middleware ({mw})", errors)

    return errors


def main():
    base_dir = Path(__file__).parent.parent
    pipelines_dir = base_dir / "bot" / "pipelines"

    print(f"Checking pipelines in: {pipelines_dir}")
    print("-" * 50)

    pipelines = load_pipelines(pipelines_dir)

    if not pipelines:
        print("No pipelines found!")
        return 1

    total_errors = 0
    valid_count = 0

    for pipeline in pipelines:
        name = pipeline.get("name", pipeline.get("_file", "unknown"))
        errors = validate_pipeline(pipeline)

        if errors:
            print(f"\nX Pipeline: {name}")
            for error in errors:
                print(error)
            total_errors += len(errors)
        else:
            print(f"✓ {name}")
            valid_count += 1

    print("-" * 50)
    print(f"Summary: {valid_count} valid, {total_errors} errors")

    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
