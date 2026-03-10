from apscheduler.schedulers.background import BackgroundScheduler

from pipeline import MyPipeline


class MyPipelineStore:
    def __init__(self, notification_config: dict = None):
        self.scheduler_master = BackgroundScheduler()
        self.scheduler_master.start()
        self._pipelines = {}
        self._notification_config = notification_config or {}

    def shutdown(self, wait: bool = True):
        """Gracefully shutdown all schedulers."""
        self.scheduler_master.shutdown(wait=wait)

    @property
    def notification_enabled(self) -> bool:
        return self._notification_config.get("telegram", {}).get("enabled", False)

    @property
    def notification_token(self) -> str:
        return self._notification_config.get("telegram", {}).get("token", "")

    @property
    def notification_chat_id(self) -> str:
        return self._notification_config.get("telegram", {}).get("chat_id", "")

    def get_pipeline(self, id):
        return self._pipelines[id]

    def serialize_pipelines(self):
        return {id: pipeline.to_dict() for id, pipeline in self._pipelines.items()}

    def get_all_pipelines(self):
        return self._pipelines

    def add_pipeline(self, pipeline_dict, tasks_callable):
        pipeline = MyPipeline(
            args=pipeline_dict,
            execution=tasks_callable,
            scheduler=self.scheduler_master,
            notification_config=self._notification_config,
        )
        self._pipelines[len(self._pipelines)] = pipeline

    def __repr__(self) -> str:
        return "\n".join([pipeline.__repr__() for pipeline in self._pipelines.values()])

    def make_json_dict(self) -> dict:
        return {"workers": [pipeline.to_dict() for pipeline in self._pipelines.values()]}
