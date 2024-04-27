from pipeline import MyPipeline
from apscheduler.schedulers.background import BackgroundScheduler


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
        self._pipelines[len(self._pipelines)] = pipeline

    def __repr__(self) -> str:
        # get all the reprs of the pipelines in the store and return them line by line
        return '\n'.join([pipeline.__repr__() for pipeline in self._pipelines.values()])
    
    def make_json_dict(self) -> dict:
        return {"workers": [pipeline.__dict__() for pipeline in self._pipelines.values()]}