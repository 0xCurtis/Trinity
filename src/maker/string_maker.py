from src.pipeline import MyPipeline

def string(pipeline: MyPipeline, args):
    print(pipeline)
    print("returning", args)
    return args