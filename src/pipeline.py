from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import os
import sys
from cron_descriptor import get_description, ExpressionDescriptor


class MyPipeline():
    def __init__(self, args, execution: list[callable], scheduler: BackgroundScheduler = None):
        self.scheduler = scheduler
        self.tasks = execution
        self.last_run = datetime.now()
        self.start_args = args
        self.description = args['description']
        self.name = args['name']
        self.add_time_based_pipeline(trigger='interval', tasks=execution, seconds=60, start_args=self.start_args)

        self.name = args['name']
        script_path = os.path.abspath(__file__)
        script_dir = os.path.dirname(script_path)
        parent_dir = os.path.dirname(script_dir)

        if not os.path.exists(os.path.join(parent_dir, "logs")):
            os.makedirs(os.path.join(parent_dir, "logs"))
        self.log_file = os.path.join(parent_dir, "logs\\" + self.name + ".log")
        # create post_history file if it doesn't exist
        if not os.path.join(parent_dir, "history"):
            os.makedirs(os.path.join(parent_dir, "history"))
        self.history_file = os.path.join(parent_dir, "history\\" + self.name + ".hist")
        with open(self.history_file, 'a') as f:
            pass
        with open(self.log_file, 'a') as f:
            f.write("Pipeline " + self.name + " created at " + str(datetime.now()) + "\n")

    def check_post_history(self, id):
        """
        if id is in the history file, return False else True
        :param id: ID to check
        """
        with open(self.history_file, 'r') as f:
            history = f.read().splitlines()
        return id in history

    def add_to_post_history(self, id):
        """
        Add id to the post history file
        :param id: ID to add
        """
        with open(self.history_file, 'a') as f:
            f.write(id + "\n")

    def log(self, message):
        with open(self.log_file, 'a') as f:
            f.write(str(datetime.now()) + " : " + message + "\n")

    def execute_pipeline(self, tasks, start_args):
        """
        Executes the tasks in the pipeline sequentially, passing the output of
        each task as the argument to the next.
        
        :param tasks: A list of tasks (functions) to execute.
        :param start_args: Initial arguments to pass to the first task.
        """
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
            # also log the line where the error occurred
            self.log("Pipeline execution failed: " + str(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.log(f"{exc_type}, {fname}, {exc_tb.tb_lineno}")
        finally:
            for media in self.result['media']:
                os.remove(media['path'])
                self.log(f"Successfully deleted {self.result['media']}")
        return self.result

    def add_media(self, media_type, path):
        """
        Adds media to the pipeline result.
        
        :param media_type: Type of media ('photo', 'video', 'animation', 'document').
        :param path: Path to the media file.
        """
        self.result['media'].append({
            "type": media_type,
            "path": path
        })

    def add_time_based_pipeline(self, tasks, trigger='interval', start_args=None, **trigger_args):
        """
        Adds a time-based pipeline to the scheduler.
        
        :param tasks: A list of tasks (functions) that form the pipeline.
        :param trigger: Type of trigger ('date', 'interval', or 'cron').
        :param start_args: Initial arguments to pass to the first task in the pipeline.
        :param trigger_args: Arguments for the trigger. E.g., seconds=10 for an interval trigger.
        """
        if start_args['instant_launch'] == True:
            self.scheduler.add_job(self.execute_pipeline, CronTrigger.from_crontab(start_args['launch_condition']['time']), id=self.name, args=[tasks, start_args], **trigger_args, next_run_time=datetime.now())
        else:
            self.scheduler.add_job(self.execute_pipeline, CronTrigger.from_crontab(start_args['launch_condition']['time']),
                               id=self.name, args=[tasks, start_args], **trigger_args)
        print(f"next run at : {self.scheduler.get_job(self.name).next_run_time}")

    def stop_scheduler(self):
        self.scheduler.shutdown()

    def __repr__(self) -> str:
        # get the nect run time of the job and return it with the desciption and name
        return f"Next run at : {self.scheduler.get_job(self.name).next_run_time} : {self.description} : {self.name}"

    def __dict__(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "next_run_time": self.scheduler.get_job(self.name).next_run_time,
            "cron_tab explaination" : get_description(self.start_args['launch_condition']['time']),
        }
