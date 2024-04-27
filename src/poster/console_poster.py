from src.pipeline import MyPipeline
from src.app import check_keys

@check_keys('string', 'media')
def console(pipeline: MyPipeline, args):
    print(args)
    return args