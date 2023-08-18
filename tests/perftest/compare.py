#!/usr/bin/env python
import os
import shutil
import pathlib
import pandas as pd

filename = 'perftest.csv'

def compare_measures(measure_dir, tagname):
    #measure_dir = os.environ.get('PERFTEST_MEASURE_DIR', '')
    path = pathlib.Path(measure_dir)
    if path.exists():
        file = path / filename
        df = pd.read_csv(file)
        compare_datasets(df, tagname)
    else:
        raise ValueError(f'Directory {measure_dir} does not exist')

def compare_datasets(df, tagname, metric_name='time'):
    df_mean = df[[tagname, metric_name]].groupby(tagname).mean()
    print(df_mean)

def clear_measures(measure_dir):
    #measure_dir = os.environ.get('PERFTEST_MEASURE_DIR', '')
    shutil.rmtree(measure_dir)

def main():
    import sys
    path = sys.argv[1]
    command = sys.argv[2]
    if command == 'clear':
        clear_measures(path)
    else:
        tagname = command[len('--tagname='):]
        compare_measures(path, tagname)
        



if __name__=="__main__":
    main()
