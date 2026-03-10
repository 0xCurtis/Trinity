import os
import sys
import traceback
from datetime import datetime
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from cron_descriptor import get_description

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from notifications import send_error_notification, send_success_notification


class MyPipeline:
    def __init__(
        self,
        args: dict,
        execution: list[callable],
        scheduler: BackgroundScheduler = None,
        notification_config: dict = None,
    ):
        self.scheduler = scheduler
        self.tasks = execution
        self.last_run = datetime.now()
        self.start_args = args
        self.description = args["description"]
        self.name = args["name"]
        self.notification_config = notification_config or {}
        self._last_run_status: str = "never"
        self._last_run_time: datetime | None = None
        self._failed_task: str = "none"
        self._last_error: str = ""

        self.add_time_based_pipeline(
            trigger="interval", tasks=execution, seconds=60, start_args=self.start_args
        )

        script_path = os.path.abspath(__file__)
        script_dir = os.path.dirname(script_path)
        parent_dir = os.path.dirname(script_dir)

        if not os.path.exists(os.path.join(parent_dir, "logs")):
            os.makedirs(os.path.join(parent_dir, "logs"))
        self.log_file = os.path.join(parent_dir, "logs", self.name + ".log")

        if not os.path.exists(os.path.join(parent_dir, "history")):
            os.makedirs(os.path.join(parent_dir, "history"))
        self.history_file = os.path.join(parent_dir, "history", self.name + ".hist")

        self._history: set[str] = self._load_history()

        with open(self.log_file, "a") as f:
            f.write("Pipeline " + self.name + " created at " + str(datetime.now()) + "\n")

    def _load_history(self) -> set[str]:
        if os.path.exists(self.history_file):
            with open(self.history_file) as f:
                return set(line.strip() for line in f if line.strip())
        return set()

    def _persist_history(self):
        with open(self.history_file, "w") as f:
            for item in self._history:
                f.write(item + "\n")

    def check_post_history(self, id: str) -> bool:
        return id in self._history

    def add_to_post_history(self, id: str):
        self._history.add(id)
        self._persist_history()

    def log(self, message: str):
        with open(self.log_file, "a") as f:
            f.write(str(datetime.now()) + " : " + message + "\n")

    def _notify_error(self, error_message: str, failed_task: str):
        if not self.notification_config.get("telegram", {}).get("enabled"):
            return

        token = self.notification_config.get("telegram", {}).get("token", "")
        chat_id = self.notification_config.get("telegram", {}).get("chat_id", "")

        if not token or not chat_id:
            return

        send_error_notification(
            token=token,
            chat_id=chat_id,
            pipeline_name=self.name,
            description=self.description,
            error_message=error_message,
            failed_task=failed_task,
            timestamp=str(self._last_run_time),
        )

    def _notify_success(self):
        if not self.notification_config.get("telegram", {}).get("enabled"):
            return

        token = self.notification_config.get("telegram", {}).get("token", "")
        chat_id = self.notification_config.get("telegram", {}).get("chat_id", "")

        if not token or not chat_id:
            return

        send_success_notification(
            token=token,
            chat_id=chat_id,
            pipeline_name=self.name,
            description=self.description,
            timestamp=str(self._last_run_time),
        )

    def execute_pipeline(self, tasks: list, start_args: dict) -> dict:
        # Base result with pipeline-level configuration
        self.result = {"string": "", "media": [], **start_args}
        self.result["_add_to_history"] = []

        source_cfg = start_args.get("source")
        # e.g. args["redgifs"] instead of args["source"]["redgifs"].
        source_cfg = start_args.get("source")
        if isinstance(source_cfg, dict):
            for key, value in source_cfg.items():
                if key != "task" and key not in self.result:
                    self.result[key] = value

        post_cfg = start_args.get("post")
        if isinstance(post_cfg, dict):
            for key, value in post_cfg.items():
                if key != "task" and key not in self.result:
                    self.result[key] = value

        self._last_run_time = datetime.now()
        failed_task = "none"

        try:
            for task in tasks:
                print("Executing task:", task.__name__)
                failed_task = task.__name__
                self.result = task(self, self.result)
            for id in self.result.get("_add_to_history", []):
                self.add_to_post_history(id)
            self._last_run_status = "success"
            self.log("Pipeline executed successfully.")
            self._notify_success()
        except Exception as e:
            self._last_run_status = "failed"
            exc_type, exc_obj, exc_tb = sys.exc_info()
            file_name = None
            line_no = None
            if exc_tb:
                file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                line_no = exc_tb.tb_lineno

            location_info = ""
            if file_name is not None and line_no is not None:
                location_info = f" (file {file_name}, line {line_no})"

            detailed_error = f"{type(e).__name__}: {e}{location_info}"

            self._last_error = detailed_error
            self._failed_task = failed_task
            self.log(f"Pipeline execution failed in task '{failed_task}': {detailed_error}")
            self.log(traceback.format_exc())
            self._notify_error(detailed_error, failed_task)
        finally:
            for media in self.result.get("media", []):
                try:
                    if os.path.exists(media["path"]):
                        os.remove(media["path"])
                        self.log(f"Successfully deleted {media['path']}")
                except Exception as cleanup_err:
                    self.log(f"Failed to delete {media.get('path', 'unknown')}: {cleanup_err}")
        return self.result

    def add_media(self, media_type: str, path: str):
        self.result["media"].append({"type": media_type, "path": path})

    def add_time_based_pipeline(
        self, tasks: list, trigger: str = "interval", start_args: dict = None, **trigger_args
    ):
        if start_args["instant_launch"]:
            self.scheduler.add_job(
                self.execute_pipeline,
                CronTrigger.from_crontab(start_args["launch_condition"]["time"]),
                id=self.name,
                args=[tasks, start_args],
                **trigger_args,
                next_run_time=datetime.now(),
            )
        else:
            self.scheduler.add_job(
                self.execute_pipeline,
                CronTrigger.from_crontab(start_args["launch_condition"]["time"]),
                id=self.name,
                args=[tasks, start_args],
                **trigger_args,
            )
        print(f"next run at : {self.scheduler.get_job(self.name).next_run_time}")

    def stop_scheduler(self):
        self.scheduler.shutdown()

    def __repr__(self) -> str:
        return (
            f"{self.scheduler.get_job(self.name).next_run_time} : {self.description} : {self.name}"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "next_run_time": self.scheduler.get_job(self.name).next_run_time,
            "cron_tab_explanation": get_description(self.start_args["launch_condition"]["time"]),
            "last_run_status": self._last_run_status,
            "last_run_time": str(self._last_run_time) if self._last_run_time else None,
            "last_error": self._last_error if self._last_run_status == "failed" else None,
        }
