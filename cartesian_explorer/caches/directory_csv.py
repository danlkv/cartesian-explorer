from .cacheIFC import CacheIFC
import pickle
from pathlib import Path
import pandas as pd
import shutil
from functools import partial
from loguru import logger

def _save_item(item, cache_file):
    with open(cache_file, 'wb') as f:
        pickle.dump(item, f)
    return cache_file

def _load_item(cache_file):
    with open(cache_file, 'rb') as f:
        return pickle.load(f)

def _lookup_item(item):
    return Path(item).exists()

def args_kwargs_merge(args, kwargs):
    kwargs = dict(kwargs)
    for i, arg in enumerate(args):
        kwargs[f'{i}'] = arg
    return kwargs

def is_simple_value(v):
    return isinstance(v, (int, str, float, bool, type(None)))

def args_kwargs_split(kwargs):
    indexed_args = []
    new_kwargs = {}
    for k, v in kwargs.items():
        try:
            indexed_args.append((int(k), v))
        except:
            new_kwargs[k] = v
    indexed_args.sort(lambda x: x[0])
    return tuple(v for _, v in indexed_args), new_kwargs

def kwargs_simplify(kwargs):
    """ Converts items in kwargs to a simple (int, float str, bool) vaule
    If the value is not simple, uses hash. 
    Values must be hashable
    """
    result = {}
    for k, v in kwargs.items():
        if is_simple_value(v):
            result[k] = v
        else:
            result[k] = hash(v)
    return result

def kwargs_to_filestr(kwargs):
    """ Converts kwargs to filename-like string """
    return '_'.join([f'{k}-{v}' for k, v in kwargs.items()])
        

class DirectoryCSVCache(CacheIFC):
    """
    Attributes:

    * path (Path): path to the cache directory
    * verbose (int): verbosity level
    * _output_name_fn - Function takes a wrapped functions and returns column name for output
    
    """
    def __init__(self, cache_path, verbose=0, output_name=lambda x: x.__name__):
        self.path = Path(cache_path)
        self.verbose = verbose
        # if output_name is a string, convert to lambda 
        if isinstance(output_name, str):
            output_fn = lambda x: output_name
        else:
            output_fn = output_name
        self._output_name_fn = output_fn

    def _get_path_for_func(self, func):
        path = self.path / func.__name__
        return path

    def wrap(self, func, **kwargs) -> callable:
        path = self._get_path_for_func(func)
        path.mkdir(parents=True, exist_ok=True)
        self._log(f"Created cache directory at {path}")
        return partial(self.call, func, **kwargs)
    
    def _log(self, *args, **kwargs):
        if self.verbose:
            logger.info(*args, **kwargs)

    def call(self, func, *args, **kwargs):
        cache_path = self._get_path_for_func(func)
        index = cache_path / 'index.csv'
        output_column = self._output_name_fn(func)
        kwargs_merged = args_kwargs_merge(args, kwargs)
        kwargs_simplified = kwargs_simplify(kwargs_merged)
        # Check if the function has been called with these args before
        row = self._lookup(index, output_column, kwargs_simplified)
        if not isinstance(row, bool):
            cachefile = row[output_column]
            self._log(f"Loading file from {cachefile}")
            result = _load_item(cachefile)
            return result
        else:
            cachefilename = kwargs_to_filestr(kwargs_simplified) + '.pkl'
            cachefile = str(cache_path / cachefilename)

        result = func(*args, **kwargs)
        self._log(f"Saving result to {cachefile}")
        cachefile_written = _save_item(result, cache_file=cachefile)
        row_new = kwargs_simplified
        row_new[output_column] = cachefile_written
        # Add the row to the index
        if not index.exists():
            index_df = pd.DataFrame(columns=row_new.keys())
            index_df.to_csv(index, index=False)
        # append to the csv file
        pd.DataFrame([row_new]).to_csv(index, mode='a', header=False, index=False)
        self._log(f"Updated index at {index} for {cachefile}")
        return result
    
    def _lookup(self, indexfile, output_column, kwargs_simplified):
        if not indexfile.exists():
            return False
        index_df = pd.read_csv(indexfile, chunksize=500)
        for chunk in index_df:
            for _, row in chunk.iterrows():
                # check that all kwargs except the output column match
                if all([row[k] == v for k, v in kwargs_simplified.items() if k != output_column]):
                    return row

        return False

    def lookup(self, func, *args, **kwargs):
        cache_path = self._get_path_for_func(func)
        index = cache_path / 'index.csv'
        output_column = self._output_name_fn(func)
        kwargs_merged = args_kwargs_merge(args, kwargs)
        kwargs_simplified = kwargs_simplify(kwargs_merged)
        row = self._lookup(index, output_column, kwargs_simplified)
        return row

    def clear(self, func):
        path = self._get_path_for_func(func)
        if path.exists():
            shutil.rmtree(path)
