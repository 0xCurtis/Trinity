import time
import random
from pipeline import MyPipeline

def delay(pipeline : MyPipeline=None, args : dict=None):
    random_delay = random.randint(1, 10)
    pipeline.log("Delay of " + str(random_delay) + " seconds.")
    time.sleep(random_delay)
    return True