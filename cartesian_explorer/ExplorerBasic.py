import numpy as np
import matplotlib.pyplot as plt
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
from functools import reduce
from itertools import repeat
from tqdm.auto import tqdm

from cartesian_explorer import caches
from cartesian_explorer import dict_product
from cartesian_explorer import parallels


from typing import Dict

def apply_func(x):
    func, kwargs = x
    return func(**kwargs)
def just_lookup(user_func, cache, kwargs):
    in_cache = cache.lookup(user_func, **kwargs)
    if in_cache:
        return user_func(**kwargs)

class ExplorerBasic:
    def __init__(self, cache_size=512, parallel='thread'
                 , cache=caches.FunctoolsCache()
                ):
        self.cache = cache if cache else None
        self.cache_size = cache_size
        self.parallel_class = None
        self.parallel = None
        if isinstance(parallel, str):
            if parallel == 'thread':
                self.parallel_class = parallels.Thread
            elif parallel == 'process':
                self.parallel_class = parallels.Multiprocess
            elif parallel == 'joblib':
                self.parallel_class = parallels.JobLib
        else:
            self.parallel = parallel

    def _get_iterarg_params(self, value):
        """ The function that converts user-provided iterable. """
        if isinstance(value, str):
            raise ValueError("Won't iterate this string")
        return list(value), len(value)

    def _iterate_subplots(self, iterargs, subplot_var_key, data):
        if subplot_var_key is not None:
            subplots = iterargs[subplot_var_key]
            f, axs = plt.subplots(1, len(subplots),
                                  figsize=(len(subplots)*4, 3), dpi=100)
            data = data.reshape(len(subplots), -1)
        else:
            subplots = [None]
            f = plt.figure(dpi=100)
            axs = [plt.gca()]
            data = data[np.newaxis, :]
        for i, (ax, subplot_val) in enumerate(zip(axs, subplots)):
            if subplot_val is not None:
                ax.set_title(f'{subplot_var_key} = {subplot_val}')
            yield f, ax, data[i]


    # -- API

    # ---- Input

    def cache_function(self, func):
        if self.cache is not None:
            if hasattr(self, 'cache_size'):
                cache_size = self.cache_size
            else:
                cache_size = 512
            func = self.cache.wrap(func, maxsize=cache_size)
        return func

    # ---- Output

    def map(self, func, processes=1, out_dim=None, pbar=True,
            **param_space: Dict[str, iter]):
        """ Apply a function cartesian product of parameters.

        Args:
            func (callable): the function to call. Should accept keyword arguments.
            processes (int): the number of processes for parallelization.
            out_dim (int): if the function returns a vector,
                specify the dimension for proper output shape.
                The vector dimension will become last dimension of the result.
            pbar (bool): whether to use the progress bar

            **kwargs (dict[str, iter]):
                each keyword argument should be an iterable.
                the order of the arguments will be preserved in the output shape.

        Returns:
            numpy.ndarray: an array of shape ``(N_i, ... [out_dim])``
                where N_i is the length of i-th iterable.

        Examples:

            >>> arr = ex.map(lambda x, y: x + y, x=[1, 2, 3], y=[3, 4], pbar=False)
            >>> arr.shape
            (3, 2)
            >>> arr
            array([[4, 5],
                   [5, 6],
                   [6, 7]])

            >>> ex.map(lambda x, y: (x, y), x=[1,3,'h'], y=[(12,0)], pbar=False)
            ValueError: Cannot reshape array of size 6 into sape (3,)

            >>> ex.map(lambda x, y: (x, y), out_dim=2, x=[1,3,'h'], y=[12], pbar=False)
            array([['1', '3', 'h'],
                   ['12', '12', '12']], dtype='<U21')

        """

        # Uses apply_func
        param_iter = dict_product(**param_space)
        result_shape = tuple(len(x) for x in param_space.values())
        result_shape = tuple(x for x in result_shape if x > 1)

        total_len = reduce(np.multiply, result_shape, 1)
        if (processes > 1 and self.parallel_class is not None) or self.parallel:
            parallel = self.parallel or self.parallel_class(processes=processes)
            result_lin = parallel.starstarmap(func, param_iter)
        else:
            if pbar:
                result_lin = list(tqdm(
                    map(lambda x: func(**x), param_iter)
                    , total=total_len
                ))
            else:
                result_lin = list(map(lambda x: func(**x), param_iter))

        # -- Convert to output array. If the element is something vector-ish,
        # use np.object dtype
        #print('result', result_lin, result_shape)
        if out_dim:
            result_shape = out_dim, *result_shape
            result_lin = np.swapaxes(result_lin, 0, -1)
        try:
            result = np.array(result_lin).reshape(result_shape)
        except (TypeError, ValueError) :
            result = np.array(result_lin, dtype=object).reshape(result_shape)
        # --
        return result

    def map_no_call(self, func, processes=1, out_dim=None,
                    **param_space: Dict[str, iter]):
        """ Get cached values of function over cartesian product of parameters.

        API is same as :meth:`cartesian_explorer.ExplorerBasic.map`
        """

        param_iter = dict_product(**param_space)
        return self.map(just_lookup, processes=processes, out_dim=out_dim,
                        user_func=[func], cache=[self.cache], kwargs=list(param_iter)
                       )

    # ---- Plotting

    def get_iterargs(self, uservars):
        """
        1. Take a dictionary of user-provided arguments
        and determine which arguments should we iterate over.

        2. Convert single-value arguments to sequences for mapping

        Parameters:
            uservars : dictionary of {key: Union[value, list[value]]}

        Returns:
            filtered dictionary with good format of value {key: list[value]}
        """
        len_x = None
        x_label = None
        var_specs = []

        uservars_corrected = {}
        for key in uservars:
            try:
                x, len_x = self._get_iterarg_params(uservars[key])
                x_label = key
                uservars_corrected[key] = uservars[key]
                if len_x == 1:
                    continue
                var_specs.append((x_label, x))
            except (LookupError, ValueError):
                uservars_corrected[key] = (uservars[key], )

        # print('selected iterargs', var_specs)
        return dict(var_specs), uservars_corrected


    def plot2d(self, func, plot_func=plt.plot, plot_kwargs=dict(), processes=1,
               **uservars):

        # -- Check input arg
        iterargs, uservars_corrected = self.get_iterargs(uservars)
        #print('iterargs', iterargs)
        plot_levels = [
            'subplots'  # Goes to third to last iterarg if exists
            ,'lines' # Goes to second to last iterarg, if exists
            ,'x-axis' # Goes to last iterarg
        ]
        plot_level_var_keys = dict(zip(
            reversed(plot_levels),
            reversed(tuple(iterargs.keys()))
        ))
        #print('plot level vars', plot_level_var_keys)

        data = self.map(func, processes=processes, **uservars_corrected)

        # -- Subplots preparation
        subplot_var_key = plot_level_var_keys.get('subplots')
        for f, ax, data in self._iterate_subplots(iterargs, subplot_var_key, data):
            plt.sca(ax)
        # --


            x_var_key = plot_level_var_keys.get('x-axis')
            x = iterargs[x_var_key]

            # -- Lines preparation
            lines_var_key = plot_level_var_keys.get('lines')
            if lines_var_key is not None:
                lines = iterargs[lines_var_key]
            else:
                lines = [None]

            for i, lineval in enumerate(lines):
                data = data.reshape(len(lines), len(x))
                if lineval is not None:
                    plot_kwargs['label'] = str(lineval)
            # --
                plot_func(x, data[i], **plot_kwargs)

            plt.legend()
            plt.xlabel(x_var_key)
        return f

    def plot3d(self, func, plot_func=plt.contourf, plot_kwargs=dict(), processes=1
               , **uservars ):

        #-- Check input arg
        iterargs, uservars_corrected = self.get_iterargs(uservars)
        plot_levels = [
            'subplots'  # Goes to third to last iterarg if exists
            ,'y' # Goes to second to last iterarg, if exists
            ,'x' # Goes to last iterarg
        ]
        plot_level_var_keys = dict(zip(
            reversed(plot_levels),
            reversed(tuple(iterargs.keys()))
        ))
        #print('plot level vars', plot_level_var_keys)
        # --

        data = self.map(func, processes=processes, **uservars_corrected)

        # -- Subplots preparation
        subplot_var_key = plot_level_var_keys.get('subplots')
        for f, ax, data in self._iterate_subplots(iterargs, subplot_var_key, data):
            plt.sca(ax)
        # --
            x_label, y_label = plot_level_var_keys['x'], plot_level_var_keys['y']
            x, y = iterargs[x_label], iterargs[y_label]

            ret = plot_func(x, y, data.reshape(len(y), len(x)), **plot_kwargs)
            plt.colorbar(ret)
            plt.xlabel(x_label)
            plt.ylabel(y_label)
        return f
