from .cacheIFC import CacheIFC
import pickle
from pathlib import Path
import pandas as pd
import shutil
from functools import partial

def serialize_item_pickle(item, cache_file):
    with open(cache_file, 'wb') as f:
        pickle.dump(item, f)
    return cache_file

def serialize_kwargs_pickle(args, kwargs, cache_dir):
    """
    Convert

        * int, str, float, bool, None -> string
        * other -> pickle to file in `cache_dir`
    """
    kwargs = dict(kwargs)
    for i, arg in enumerate(args):
        kwargs[f'{i}'] = arg

    simple_fields = {}
    complex_fields = {}
    for k, v in kwargs.items():
        if isinstance(v, (int, str, float, bool, type(None))):
            simple_fields[k] = v
        else:
            complex_fields[k] = v

    simple_field_str = [f'{k}_{v}' for k, v in simple_fields.items()]
    for k, v in complex_fields.items():
        cache_file = cache_dir / f'{k}__{simple_field_str}.pickle'
        filename = serialize_item_pickle(v, cache_file)
        simple_fields[k] = filename
    return simple_fields


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
        return partial(self.call, func, **kwargs)

    def call(self, func, *args, **kwargs):
        path = self._get_path_for_func(func)
        index = path / 'index.csv'
        # Convert function, args and kwargs to lookup row
        simple_kwargs = simplify_kwargs_pickle(args, kwargs, path)
        # Check if the function has been called with these args before
        output_column = self._output_name_fn(func)
        if self.lookup(func, *args, **kwargs):
        row = index.exists()
        if row is not None:
            result = load_pickle(row[output_column])
            return result
        # If not, call the function
        result = func(*args, **kwargs)
        # Save the result to the cache
        row = simple_kwargs
        row[output_column] = result
        row_serialized = serialize_kwargs_pickle(row, path)
        # Add the row to the index
        if not index.exists():
            index_df = pd.DataFrame(columns=row.keys())
            # save the index
            index_df.to_csv(index, index=False)
        # append to the csv file
        pd.DataFrame([row_serialized]).to_csv(index, mode='a', header=False, index=False)
        return result

    def lookup(self, func, *args, **kwargs):
        path = self._get_path_for_func(func)
        index = path / 'index.csv'
        # TODO: actually check the complex fields
        converted_kwargs = serialize_kwargs_pickle(args, kwargs, path)
        if not index.exists():
            return False
        index_df = pd.read_csv(index, chunksize=500)
        for chunk in index_df:
            for _, row in chunk.iterrows():
                # check that all kwargs except the output column match
                output_column = self._output_name_fn(func)
                if all([row[k] == v for k, v in converted_kwargs.items() if k != output_column]):
                    return row

        return False


    def clear(self, func):
        path = self._get_path_for_func(func)
        if path.exists():
            shutil.rmtree(path)
