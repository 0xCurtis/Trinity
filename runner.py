import importlib
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

from src.config import load_pipeline_config

load_dotenv()

APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(APP_DIR / "src"))

_imghdr_path = APP_DIR / "src" / "imghdr.py"
if _imghdr_path.exists():
    from importlib.util import module_from_spec, spec_from_file_location

    spec = spec_from_file_location("imghdr", str(_imghdr_path))
    _imghdr = module_from_spec(spec)
    spec.loader.exec_module(_imghdr)
    sys.modules["imghdr"] = _imghdr

from src.pipeline_store import MyPipelineStore

_shutdown_requested = False
_scheduler: MyPipelineStore | None = None


def _signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global _shutdown_requested
    sig_name = signal.Signals(signum).name
    print(f"\nReceived {sig_name}, initiating graceful shutdown...")
    _shutdown_requested = True
    if _scheduler:
        print("Shutting down schedulers...")
        _scheduler.shutdown()


def _setup_signal_handlers():
    """Setup handlers for graceful shutdown."""
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)


def load_configs(pipelines_dir: Path) -> list[dict]:
    """Load all JSON configs from pipelines directory."""
    configs = []
    if not pipelines_dir.exists():
        print(f"Pipelines directory not found: {pipelines_dir}")
        return configs

    for file in pipelines_dir.glob("*.json"):
        if file.stem == "global":
            continue
        try:
            config = load_pipeline_config(file)
            config["_file"] = file.stem
            configs.append(config)
        except Exception as e:
            print(f"Error loading {file}: {e}")
    return configs


def get_notification_config(pipelines_dir: Path) -> dict:
    """Load notification config from pipelines directory."""
    global_config = pipelines_dir / "global.json"
    if global_config.exists():
        config = load_pipeline_config(global_config)
        return config.get("notifications", {})
    return {}


def should_run(pipeline_config: dict, last_run_file: Path) -> bool:
    """Check if pipeline should run based on interval/cron."""
    if not last_run_file.exists():
        return True

    with open(last_run_file) as f:
        last_run = datetime.fromisoformat(f.read().strip())

    interval = pipeline_config.get("run_every_minutes", 15)

    next_run = last_run + timedelta(minutes=interval)

    return datetime.now() >= next_run


def update_last_run(pipeline_config: dict, last_run_file: Path):
    """Update last run timestamp."""
    with open(last_run_file, "w") as f:
        f.write(datetime.now().isoformat())


def load_function(full_function_path: str):
    """Dynamically loads a function given its full path."""
    module_path, function_name = full_function_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, function_name)


def run_pipeline(pipeline_config: dict, notification_config: dict, history_dir: Path):
    """Run a single pipeline."""
    name = pipeline_config.get("name", "unnamed")
    print(f"\n{'=' * 50}")
    print(f"Running pipeline: {name}")
    print(f"{'=' * 50}")

    # Add required fields for backward compatibility with pipeline
    pipeline_config.setdefault("instant_launch", False)
    pipeline_config.setdefault("launch_condition", {"time": "*/15 * * * *"})

    # Load tasks
    tasks = []
    try:
        tasks = [load_function(pipeline_config["source"]["task"])]
        tasks += [load_function(m) for m in pipeline_config.get("middleware", [])]
        tasks.append(load_function(pipeline_config["post"]["task"]))
    except Exception as e:
        print(f"Error loading tasks for {name}: {e}")
        return

    # Create minimal pipeline store with notification config
    store = MyPipelineStore(notification_config=notification_config)

    # Add pipeline
    try:
        store.add_pipeline(pipeline_config, tasks)
    except Exception as e:
        print(f"Error adding pipeline {name}: {e}")
        return

    # Execute
    try:
        pipeline = list(store.get_all_pipelines().values())[0]
        pipeline.execute_pipeline(tasks, pipeline_config)
    except Exception as e:
        print(f"Error executing pipeline {name}: {e}")


def main():
    """Main runner - loads all configs and runs due pipelines."""
    global _scheduler, _shutdown_requested
    _setup_signal_handlers()

    pipelines_dir = APP_DIR / "pipelines"
    history_dir = APP_DIR / "history"
    last_run_dir = APP_DIR / ".last_run"

    # Ensure directories exist
    history_dir.mkdir(exist_ok=True)
    last_run_dir.mkdir(exist_ok=True)

    # Load configs
    configs = load_configs(pipelines_dir)
    if not configs:
        print("No pipeline configs found")
        return

    # Load notification config
    notification_config = get_notification_config(pipelines_dir)

    print(f"Found {len(configs)} pipeline configs")
    print(
        f"Notifications: {'enabled' if notification_config.get('telegram', {}).get('enabled') else 'disabled'}"
    )

    # Run due pipelines
    ran = 0
    for config in configs:
        if _shutdown_requested:
            print("Shutdown requested, stopping pipeline execution")
            break

        name = config.get("name", "unnamed")

        # Check if enabled
        if not config.get("enabled", True):
            print(f"Skipping disabled: {name}")
            continue

        # Check if should run
        last_run_file = last_run_dir / f"{name}.lastrun"
        if not should_run(config, last_run_file):
            continue

        # Run pipeline
        run_pipeline(config, notification_config, history_dir)
        update_last_run(config, last_run_file)
        ran += 1

    print(f"\nRan {ran} pipeline(s)")


if __name__ == "__main__":
    main()
