# app.py
import json
import sys

sys.path.append('src')
from pipeline_store import MyPipelineStore
from maker import *
from poster import *
import importlib
from common.models.base import Base, engine
from argparse import ArgumentParser
from alembic.config import Config
from alembic import command
import os
from common.models.pipelines_infos import PipelineInfos
from common.models.base import Session


def run_migrations(is_local=False):
    file_name = 'alembic_local.ini' if is_local else 'alembic_prod.ini'
    alembic_ini_path = os.path.join(os.path.dirname(__file__), '..', file_name)
    alembic_cfg = Config(alembic_ini_path)
    command.upgrade(alembic_cfg, 'head')

def load_function(full_function_path):
    module_path, function_name = full_function_path.rsplit('.', 1)
    module = importlib.import_module(module_path)
    function = getattr(module, function_name)
    return function

def setup_store(debug=False) -> MyPipelineStore:
    store = MyPipelineStore()

    # Load existing pipelines from the database
    existing_pipelines = store.load_existing_pipelines()

    with open('data.json', 'r', encoding='utf-8') as conf:
        data = conf.read()
        json_dict = json.loads(data)
        pipelines = json_dict['workers']

        new_pipeline_names = set()
        for pipeline_dict in pipelines:
            if not pipeline_dict['enabled']:
                continue
            new_pipeline_names.add(pipeline_dict['name'])
            tasks = [pipeline_dict["source"]["task"]] + pipeline_dict["middleware"] + [pipeline_dict["post"]["task"]]
            tasks_callable = [load_function(task) for task in tasks]
            print(f"Adding : {pipeline_dict['name']}")
            store.add_pipeline(pipeline_dict, tasks_callable)

    # Remove obsolete pipelines
    for existing_pipeline_name in existing_pipelines:
        if existing_pipeline_name not in new_pipeline_names:
            print(f"Removing obsolete pipeline: {existing_pipeline_name}")
            store.remove_pipeline(existing_pipeline_name)
            session = Session()
            session.query(PipelineInfos).filter(PipelineInfos.name == existing_pipeline_name).delete()
            session.commit()
    return store

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('--test', action='store_true', default=False, help='Run the app in test mode')
    args = parser.parse_args()
    run_migrations(is_local=args.test)
    store = setup_store(debug=args.test)
    Base.metadata.create_all(bind=engine)
    print(store)
    import time 
    try:
        while True:
            print("Main thread sleeping")
            time.sleep(55)
    except (KeyboardInterrupt, SystemExit):
        for scheduler in store.get_all_pipelines().values():
            scheduler.shutdown()
