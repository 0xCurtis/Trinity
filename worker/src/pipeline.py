# pipeline.py
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import os
import sys
from common.models.base import Session
from common.models.log_base import LogEntry
from common.models.history import MediaHistory
from common.models.pipelines_infos import PipelineInfos
from cron_descriptor import get_description, ExpressionDescriptor
import traceback


class MyPipeline():
    def __init__(self, args, execution: list[callable], scheduler: BackgroundScheduler = None):
        self.scheduler = scheduler
        self.tasks = execution
        self.last_run = datetime.now()
        self.start_args = args
        self.description = args['description']
        self.name = args['name']
        self.add_time_based_pipeline(trigger='interval', tasks=execution, seconds=60, start_args=self.start_args)

        self.session = Session()
        self.pipeline_db = self.session.query(PipelineInfos).filter(PipelineInfos.name == self.name).first()
        if self.pipeline_db:
            self.pipeline_db.description = self.description
            self.pipeline_db.source = self.tasks[0].__name__
            self.pipeline_db.middleware = ",".join([task.__name__ for task in self.tasks[1:-1]])
            self.pipeline_db.post = self.tasks[-1].__name__
            self.pipeline_db.trigger = 'interval'
            self.pipeline_db.next_run = self.scheduler.get_job(self.name).next_run_time
        else:
            self.pipeline_db = PipelineInfos(
                name=self.name,
                description=self.description,
                source=self.tasks[0].__name__,
                middleware=",".join([task.__name__ for task in self.tasks[1:-1]]),
                post=self.tasks[-1].__name__,
                trigger='interval',
                next_run=self.scheduler.get_job(self.name).next_run_time
            )

        self.session.add(self.pipeline_db)
        self.session.commit()

    def check_post_history(self, id):
        return self.session.query(MediaHistory).filter(MediaHistory.pipeline_name == self.name, MediaHistory.media_id == id).count() > 0

    def add_to_post_history(self, id):
        log_entry = MediaHistory(pipeline_name=self.name, media_id=id)
        self.session.add(log_entry)
        self.session.commit()

    def log(self, message, level='INFO'):
        try:
            log_entry = LogEntry(source=self.name, level=level, message=message)
            self.session.add(log_entry)
            self.session.commit()
        except Exception as file_error:
            self.session.rollback()
            with open('error.log', 'a') as f:
                f.write(f"{datetime.now()} : {message}\n")
                f.write(f"Failed to write log to database: {file_error}\n")

    def execute_pipeline(self, tasks, start_args):
        self.result = {
            "string": "",
            "media": [],
            **start_args
        }
        try:
            for task in tasks:
                print('Executing task:', task.__name__)
                self.result = task(self, self.result)
            self.log("Pipeline executed successfully.")
        except Exception as e:
            self.session.rollback()  # Ensure rollback on error
            self.log("Pipeline execution failed: " + str(e), level='ERROR')
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.log(f"{exc_type}, {fname}, {exc_tb.tb_lineno}", level='ERROR')
            full_traceback = ''.join(traceback.format_exception(exc_type, exc_obj, exc_tb))
            self.log(full_traceback, level='ERROR')
        finally:
            for media in self.result.get('media', []):
                try:
                    os.remove(media['path'])
                    self.log(f"Successfully deleted {media['path']}")
                except FileNotFoundError:
                    self.log(f"File not found: {media['path']}")
                except Exception as e:
                    self.log(f"Error deleting file {media['path']}: {str(e)}")
        
        self.pipeline_db = self.session.query(PipelineInfos).filter(PipelineInfos.name == self.name).first()
        self.pipeline_db.last_run = datetime.now()
        self.pipeline_db.next_run = self.scheduler.get_job(self.name).next_run_time
        self.session.commit()
        print(f"Posted on account : {self.name}\nNext run at : {self.scheduler.get_job(self.name).next_run_time}")
        return self.result

    def add_media(self, media_type, path):
        if not hasattr(self, 'result'):
            self.result = {"string": "", "media": []}
        self.result['media'].append({
            "type": media_type,
            "path": path
        })

    def add_time_based_pipeline(self, tasks, trigger='interval', start_args=None, **trigger_args):
        if start_args['instant_launch']:
            next_run_time = datetime.now()
        else:
            next_run_time = None

        try:
            cron_trigger = CronTrigger.from_crontab(start_args['launch_condition']['time'])
        except ValueError as e:
            self.log(f"Invalid cron expression: {start_args['launch_condition']['time']} - {str(e)}")
            raise

        self.scheduler.add_job(self.execute_pipeline, cron_trigger,
                               id=self.name, args=[tasks, start_args], **trigger_args, next_run_time=next_run_time)
        print(f"Next run at: {self.scheduler.get_job(self.name).next_run_time}")

    def stop_scheduler(self):
        # Stop the specific job and perform any necessary cleanup
        job = self.scheduler.get_job(self.name)
        if job:
            job.remove()
        print(f"Scheduler for pipeline {self.name} stopped.")

    def __repr__(self) -> str:
        return f"Next run at : {self.scheduler.get_job(self.name).next_run_time} : {self.description} : {self.name}"

    def __dict__(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "next_run_time": self.scheduler.get_job(self.name).next_run_time,
            "cron_tab explanation": get_description(self.start_args['launch_condition']['time']),
        }
