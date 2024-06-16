import json
import sys

sys.path.append('src')
from pipeline_store import MyPipelineStore
from maker import *
from poster import *
import importlib
from models.base import Base, engine, Session
from argparse import ArgumentParser
from alembic.config import Config
from alembic import command
import os
from models.base import Session
from models.pipelines_infos import PipelineInfos

def run_migrations(is_local=False):
    file_name = 'alembic_local.ini' if is_local else 'alembic_prod.ini'
    alembic_ini_path = os.path.join(os.path.dirname(__file__), '..', file_name)
    alembic_cfg = Config(alembic_ini_path)
    command.upgrade(alembic_cfg, 'head')


def load_function(full_function_path):
    """
    Dynamically loads and returns a function given its full path.
    
    :param full_function_path: String with the full path to the function, e.g., 'module.submodule.function'.
    :return: The callable function.
    """
    module_path, function_name = full_function_path.rsplit('.', 1)
    module = importlib.import_module(module_path)
    function = getattr(module, function_name)
    return function

# TODO : Fix this shit
def check_keys(*keys):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for key in keys:
                if key not in args[1]:
                    raise Exception("Key " + key + " not found in args")
            return func(*args, **kwargs)

        return wrapper

    return decorator

def setup_store(debug=False):
    store = MyPipelineStore()

    pipelines_info = Session.query(PipelineInfos).all()
    for pipeline_info in pipelines_info:
        pipeline_info.enabled = False
    Session.commit()
    exit(0)
    
    with open('data.json', 'r', encoding='utf-8') as conf:
        data = conf.read()
        json_dict = json.loads(data)
        pipelines = json_dict['workers']

        for pipeline_dict in pipelines:
            if not pipeline_dict['enabled']:
                continue
            tasks = [pipeline_dict["source"]["task"]] + pipeline_dict["middleware"] + [pipeline_dict["post"]["task"]]
            tasks_callable = [load_function(task) for task in tasks]
            store.add_pipeline(pipeline_dict, tasks_callable)



if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument('--test', action='store_true', default=False, help='Run the app in test mode')
    args = parser.parse_args()
    run_migrations(is_local=args.test)
    store = setup_store(debug=args.test)
    Base.metadata.create_all(bind=engine)

    while True:
        pass
