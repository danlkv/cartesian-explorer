import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
from functools import reduce
from itertools import repeat
from tqdm.auto import tqdm

from cartesian_explorer import caches
from cartesian_explorer import dict_product
from cartesian_explorer import parallels


from typing import Dict

def _plot_with_band(x, line_data, **plot_kwargs):
    line_data = line_data.astype(np.float64)
    #maximums = np.nanmax(line_data, axis=-1)
    #minimums = np.nanmin(line_data, axis=-1)

    std = np.nanstd(line_data, axis=-1)
    mean = np.nanmean(line_data, axis=-1)
    # --
    # call the plotting function
    plt.plot(x, mean, **plot_kwargs)
    fill_kwargs = dict(
        alpha=0.05, color=plot_kwargs.get('color')
    )
    #plt.fill_between(x, minimums, maximums, **fill_kwargs)
    #plot_func(x, minimums, alpha=0.3, **line_local_plot_kwargs)
    #plot_func(x, maximums, alpha=0.3, **line_local_plot_kwargs)
    #plt.fill_between(x, mean-2*std, mean+2*std, **fill_kwargs)
    plt.fill_between(x, mean-std, mean+std, **fill_kwargs)

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
            elif parallel == 'ray':
                self.parallel_class = parallels.Ray
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
                ax.set_title(f'{subplot_val}')
            yield f, ax, data[i]


    # -- API

    # ---- Input

    def cache_function(self, func):
        if self.cache is not None:
            if hasattr(self, 'cache_size'):
                cache_size = self.cache_size
            else:
                cache_size = 512
            func = self.cache(func, maxsize=cache_size)
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

    def plot(self, func, plot_func=_plot_with_band, plot_kwargs=dict(), processes=1,
             distribution_var=tuple(),
             **uservars
            ):

        # -- Check input arg
        iterargs, uservars_corrected = self.get_iterargs(uservars)

        if isinstance(distribution_var, str):
            distribution_var = tuple([distribution_var,])

        plot_levels = [
            'subplots'  # Goes to third to last iterarg if exists
            ,'lines' # Goes to second to last iterarg, if exists
            ,'x-axis' # Goes to last iterarg
        ]
        distr_levels = [f'distr_{x}' for x in distribution_var]
        plot_levels += distr_levels
        plot_level_var_keys = dict(zip(
            reversed(tuple(iterargs.keys()))
        ))

        distribution_dims = len(distribution_var)

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
                legend_title = lines_var_key
            else:
                lines = [None]
                legend_title = None

            data = data.reshape(len(lines), len(x), -1)
            for i, lineval in enumerate(lines):
                line_local_plot_kwargs = {}
                if lineval is not None:
                    # A: Use name = value format
                    # plot_kwargs['label'] = f"{lines_var_key} = {str(lineval)}"
                    # B: Use value format
                    plot_kwargs['label'] = f"{str(lineval)}"

                    # ---- Set line color
                    _default_cmap = mpl.cm.get_cmap('gnuplot2')
                    _cmap = plot_kwargs.get('cmap', _default_cmap)
                    _c_value = i/(len(lines) - 1)
                    # Do not include edges
                    _edge_shift = .24
                    _c_value = _c_value*(1 - 2*_edge_shift) + _edge_shift
                    _default_color = _cmap(_c_value)
                    line_local_plot_kwargs['color'] = _default_color
                    # ---- 

            # --
                if plot_kwargs.get('grid', True):
                    plt.grid(True, color="0.9", which='major')
                    plt.grid(True, color="0.95", which='minor')
                # -- Handle distribution 
                line_data = data[i]
                # --
                # call the plotting function
                plot_func(x, line_data, **{**plot_kwargs, **line_local_plot_kwargs})

            if legend_title is not None:
                plt.legend(title=legend_title)
            plt.xlabel(x_var_key)
        return f


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
                legend_title = lines_var_key
            else:
                lines = [None]
                legend_title = None

            data = data.reshape(len(lines), len(x))
            for i, lineval in enumerate(lines):
                line_local_plot_kwargs = {}
                if lineval is not None:
                    # A: Use name = value format
                    # plot_kwargs['label'] = f"{lines_var_key} = {str(lineval)}"
                    # B: Use value format
                    plot_kwargs['label'] = f"{str(lineval)}"

                    # ---- Set line color
                    _default_cmap = mpl.cm.get_cmap('gnuplot2')
                    _cmap = plot_kwargs.get('cmap', _default_cmap)
                    _c_value = i/(len(lines) - 1)
                    # Do not include edges
                    _edge_shift = .24
                    _c_value = _c_value*(1 - 2*_edge_shift) + _edge_shift
                    _default_color = _cmap(_c_value)
                    line_local_plot_kwargs['color'] = _default_color
                    # ---- 

            # --
                if plot_kwargs.get('grid', True):
                    plt.grid(True, color="0.9", which='major')
                    plt.grid(True, color="0.95", which='minor')
                # call the plotting function
                plot_func(x, data[i], **{**plot_kwargs, **line_local_plot_kwargs})

            if legend_title is not None:
                plt.legend(title=legend_title)
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
