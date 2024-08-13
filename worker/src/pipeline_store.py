from pipeline import MyPipeline
from apscheduler.schedulers.background import BackgroundScheduler
from common.models.pipelines_infos import PipelineInfos
from common.models.base import Session


class MyPipelineStore():
    def __init__(self):
        self.scheduler_master = BackgroundScheduler()
        self.scheduler_master.start()
        self._pipelines = {}

    def get_pipeline(self, id):
        return self._pipelines[id]

    def serialize_pipelines(self):
        return {id: pipeline.__dict__() for id, pipeline in self._pipelines.items()}

    def get_all_pipelines(self):
        return self._pipelines

    def add_pipeline(self, pipeline_dict, tasks_callable):
        pipeline = MyPipeline(args=pipeline_dict, execution=tasks_callable, scheduler=self.scheduler_master)
        self._pipelines[pipeline_dict['name']] = pipeline

    def remove_pipeline(self, name):
        if name in self._pipelines:
            self._pipelines[name].stop_scheduler()
            del self._pipelines[name]

    def load_existing_pipelines(self):
        # Load existing pipelines from the database
        session = Session()
        existing_pipelines = session.query(PipelineInfos).all()
        return {pipeline.name: pipeline for pipeline in existing_pipelines}

    def __repr__(self) -> str:
        return '\n'.join([pipeline.__repr__() for pipeline in self._pipelines.values()])

    def make_json_dict(self) -> dict:
        return {"workers": [pipeline.__dict__() for pipeline in self._pipelines.values()]}