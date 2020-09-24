import numpy as np
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
from functools import update_wrapper
from cartesian_explorer import caches
from cartesian_explorer import dict_product

from typing import Dict

class Explorer:
    def __init__(self, use_cache=True, parallel='thread'):
        self.cache = caches.FunctoolsCache() if use_cache else None
        if parallel=='thread':
            self.Pool = ThreadPool
        elif parallel=='process':
            self.Pool = Pool
        else:
            self.Pool = None

        self._variable_providers = {}
        self._function_requires = {}

    def _register_provider(self, func, provides, requires):
        for var in provides:
            self._variable_providers[var] = func
        self._function_requires[func] = requires

    #-- API
    #---- Input

    def cache_function(self, func):
        if self.cache is not None:
            func = self.cache.wrap(func)
        return func

    def add_function(self, provides: tuple, requires=tuple()):
        def func_wrapper(user_function):
            func = self.cache_function(user_function)
            self._register_provider(func, provides, requires)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper
        return func_wrapper

    #---- Output

    def map(self, func, processes=1, **param_space: Dict[str, iter]):
        param_iter = dict_product(**param_space)
        if processes > 1 and self.Pool is not None:
            with self.Pool(processes=processes) as pool:
                data = np.array(pool.map(lambda x: func(**x), param_iter))
        else:
            data = np.array(list(map(lambda x: func(**x), param_iter)))
        return data


