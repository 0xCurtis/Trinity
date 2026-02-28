from src.pipeline import MyPipeline


def check_keys(*keys):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for key in keys:
                if key not in args[1]:
                    raise Exception("Key " + key + " not found in args")
            return func(*args, **kwargs)

        return wrapper

    return decorator


@check_keys("string", "media")
def console(pipeline: MyPipeline, args):
    print(args)
    return args
