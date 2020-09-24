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

class ExplorerBasic:
    def __init__(self, cache=caches.FunctoolsCache(), parallel='thread'):
        self.cache = cache if cache else None
        if parallel=='thread':
            self.Pool = ThreadPool
        elif parallel=='process':
            self.Pool = Pool
        else:
            self.Pool = None


    #-- API
    #---- Input

    def cache_function(self, func):
        if self.cache is not None:
            func = self.cache.wrap(func)
        return func

    #---- Output

    def map(self, func, processes=1, **param_space: Dict[str, iter]):
        # Uses apply_func
        param_iter = dict_product(**param_space)
        print('param_space',param_space)
        result_shape = tuple(len(x) for x in param_space.values())
        if processes > 1 and self.Pool is not None:
            with self.Pool(processes=processes) as pool:
                result = np.array(pool.starmap(
                    apply_func, zip(repeat(func), param_iter))
                )
        else:
            result = np.array(list(map(lambda x: func(**x), param_iter)))
        print('result', result, result_shape)
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

    def get_xy_iterargs(self, var_iter):
        len_x = None
        x_label = y_label = None
        x = []
        y = []
        for key in var_iter:
            try:
                if len_x is None:
                    if isinstance(var_iter[key], str):
                        raise ValueError("Won't iterate this string")
                    len_x = len(var_iter[key])
                    x = list(var_iter[key])
                    x_label = key
                else:
                    y = list(var_iter[key])
                    y_label = key
            except Exception:
                var_iter[key] = (var_iter[key], )

        return x, y, x_label, y_label

    def plot2d(self, func, plt_func=plt.plot, plot_kwargs=dict(), **var_iter ):
        p_len = len(var_iter)
        assert p_len <= 2, '2d plot supports no more than 2 input variables'


        #-- Check input arg
        x, y, x_label, y_label  = self.get_xy_iterargs(var_iter)
        data = self.map(func, **var_iter)

        if y_label is None:
            plt_func(x, data.reshape(len(x)), **plot_kwargs)
        else:
            for i, yval in enumerate(y):
                plot_kwargs['label'] = str(yval)
                plt_func(x, data.reshape(len(x), len(y))[i], **plot_kwargs)
        plt.legend()
        plt.xlabel(x_label)

    def plot3d(self, func, plt_func=plt.contourf, plot_kwargs=dict(), **var_iter ):
        assert len(var_iter) == 2, '3d plot supports only two input variables'

        #-- Check input arg
        x, y, x_label, y_label = self.get_xy_iterargs(var_iter)

        data = self.map(func, **var_iter).T
        plt_func(x, y, data.reshape(len(y), len(x)), **plot_kwargs)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
