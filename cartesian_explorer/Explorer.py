import numpy as np
import matplotlib.pyplot as plt
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
from functools import update_wrapper
from itertools import repeat

from cartesian_explorer import caches
from cartesian_explorer import dict_product


from typing import Dict

def apply_func(func, kwargs):
    return func(**kwargs)
def just_lookup(func, cache, kwargs):
    in_cache = cache.lookup(func, **kwargs)
    if in_cache:
        return func(**kwargs)

class Explorer:
    def __init__(self, cache=caches.FunctoolsCache(), parallel='thread'):
        self.cache = cache if cache else None
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
        # Uses apply_func
        param_iter = dict_product(**param_space)
        result_shape = tuple(len(x) for x in param_space.values())
        if processes > 1 and self.Pool is not None:
            with self.Pool(processes=processes) as pool:
                result = np.array(pool.starmap(
                    apply_func, zip(repeat(func), param_iter))
                )
        else:
            result = np.array(list(map(lambda x: func(**x), param_iter)))
        return result.reshape(result_shape)

    def map_no_call(self, func, processes=1, **param_space: Dict[str, iter]):
        # Uses just_lookup 
        param_iter = dict_product(**param_space)
        result_shape = tuple(len(x) for x in param_space.values())
        if processes > 1 and self.Pool is not None:
            with self.Pool(processes=processes) as pool:
                result = np.array(pool.starmap(
                    just_lookup, zip(repeat(func), repeat(self.cache), param_iter))
                )
        else:
            result = np.array(list(map(lambda x: just_lookup(func, self.cache, x), param_iter)))
        return result.reshape(result_shape)

    #---- Plotting

    def plot2d(self, func, plt_func=plt.plot, plot_kwargs=dict(), **var_iter ):
        assert len(var_iter) == 1, '2d plot supports only one input variable'

        #-- Check input arg
        len_x = None
        x_label = None
        x = []
        for key in var_iter:
            try:
                len_x = len(var_iter[key])
                x = list(var_iter[key])
                x_label = key
            except Exception:
                var_iter[key] = (var_iter[key], )

        data = self.map(func, **var_iter)
        plt_func(x, data.reshape(len_x), **plot_kwargs)
        plt.xlabel(x_label)

    def plot3d(self, func, plt_func=plt.contourf, plot_kwargs=dict(), **var_iter ):
        assert len(var_iter) == 2, '3d plot supports only two input variables'

        #-- Check input arg
        len_x = len_y = None
        x_label = y_label = None
        x = []
        y = []
        for key in var_iter:
            try:
                if len_x is None:
                    len_x = len(var_iter[key])
                    x = list(var_iter[key])
                    x_label = key
                else:
                    len_y = len(var_iter[key])
                    y = list(var_iter[key])
                    y_label = key

            except Exception:
                var_iter[key] = (var_iter[key], )

        data = self.map(func, **var_iter)
        plt_func(x, y, data.reshape(len_x, len_y), **plot_kwargs)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
