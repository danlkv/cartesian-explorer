import pandas as pd
import os
import time
import logging
import pathlib
logger = logging.getLogger('perftest')
logger.setLevel(logging.DEBUG)

# -- Tag utils
import subprocess
from functools import lru_cache

def get_git_revision_hash() -> str:
    return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()

def get_git_revision_short_hash() -> str:
    return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()

def get_git_branch() -> str:
    return subprocess.check_output(['git', 'branch', '--show-current']).decode('ascii').strip()
@lru_cache

def get_default_tags(func):
    #runid = str(uuid.uuid4())[:8]
    timestamp = time.time()
    return dict(
        commit_short_hash=get_git_revision_short_hash(),
        git_branch=get_git_branch(),
        name=func.__name__,
        timestamp=timestamp
    )

# -- Measure utils

FILENAME = 'perftest.csv'
MEASURE_DIR = os.environ.get('PERFTEST_MEASURE_DIR', '/tmp/py_perfmeasure_dir/')

def set_measure_directory(mdir:str):
    global MEASURE_DIR
    MEASURE_DIR = mdir
    os.environ['PERFTEST_MEASURE_DIR'] = mdir

RUNS = []
RUN_DF = None

@lru_cache
def init_runs():
    dir = pathlib.Path(MEASURE_DIR)
    measure_file = dir / FILENAME
    if measure_file.exists():
        df = pd.read_csv(measure_file)
        global RUNS
        RUNS = df.to_dict('records')


def get_measures():
    return pd.DataFrame(RUNS)

def save_measures():
    dir = pathlib.Path(MEASURE_DIR)
    measure_file = dir / FILENAME
    measure_file.parent.mkdir(exist_ok=True, parents=True)
    df = pd.DataFrame(RUNS)
    df.to_csv(measure_file)

def save_metric(tags, metric_name, metric_value):
    global RUNS
    init_runs()
    row = {metric_name:metric_value, **tags}
    logger.log(10, f'Saving {row}')
    RUNS.append(row)

def measure_time_once(func, args=tuple(), kwargs=dict(), tags=dict()):
    start = time.time()
    result = func(*args, **kwargs)
    end = time.time()
    tags = {**get_default_tags(func), **tags}
    save_metric(tags, 'time', end-start)
    return result
