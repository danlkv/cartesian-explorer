import matplotlib.pyplot as plt
from typing import Union

from cartesian_explorer.ExplorerBasic import ExplorerBasic
from functools import update_wrapper
from cartesian_explorer.lib.lru_cache import lru_cache
from cartesian_explorer.lib.dep_graph import dep_graph, draw_dependency_graph
from cartesian_explorer.lib.argument_inspect import get_required_argnames, get_optional_argnames
from cartesian_explorer import lazy_imports

RESOLVER_RECURSION_DEPTH = 15
class RecursionLimit(RuntimeError):
    pass

def limit_recurse(limit=10):
    def limit_wrapper(func):
        ncalls = 0
        def wrapper(*args, **kwargs):
            nonlocal ncalls
            ncalls += 1
            if ncalls > limit:
                ncalls = 0
                raise RecursionLimit(f"Recursion limit of {limit} exceeded")
            ret = func(*args, **kwargs)
            ncalls = 0
            return ret
        update_wrapper(wrapper, func)
        return wrapper
    return limit_wrapper

class Explorer(ExplorerBasic):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._clear_functions()

    def _clear_functions(self):
        self._variable_providers = {}
        self._function_requires = {}
        self._function_provides = {}


    def _register_provider(self, func, provides, requires):
        for var in provides:
            self._variable_providers[var] = func
        self._function_provides[func] = list(provides)
        self._function_requires[func] = list(requires)
        self._resolve_call.cache_clear()

    def set_cache(self, cache):
        """ Set new cache provider for all registered functions
        Args:
            cache (cartesian_explorer.caches.cacheIFC): a cache to use.
        """
        self.cache = cache
        functions, provides = zip(*self._function_provides.items())
        _, requires = zip(*self._function_requires.items())
        self._clear_functions()
        for maybe_cached_func, req, prov in zip(functions, requires, provides):
            try:
                func = maybe_cached_func._original
            except AttributeError:
                func = maybe_cached_func

            self._register_provider(func, prov, req)

    def get_provided(self):
        """ Return all variable names provided by all registered providers. """
        return list(sum(self._function_provides.values(), []))

    def _resolve_1(self, requires):
        funcs_to_call = []
        next_requires = []
        for var in requires:
            try:
                var_provider = self._variable_providers[var]
                this_requires = self._function_requires[var_provider]
                if var in this_requires:
                    raise ValueError(f'Failed to resolve: depth-1 circular dependency of {var} in {var_provider}')
                next_requires += this_requires

            except KeyError:
                continue

            funcs_to_call.append(var_provider)

        #print('fu', funcs_to_call)
        return tuple(set(funcs_to_call)), tuple(set(next_requires))

    @lru_cache
    @limit_recurse(limit=RESOLVER_RECURSION_DEPTH)
    def _resolve_call(self, need, have, func_to_call=tuple()):
        #print('resolving', need, 'have', have)
        have = set(have)
        vars_left = set(need) - set(have)
        if len(vars_left)==0:
            return func_to_call
        else:
            next_funcs, next_requires = self._resolve_1(vars_left)
            #print('next', next_funcs, next_requires)
            if any(x in vars_left for x in next_requires):
                # could be not only in case of circular dependency :
                #        .->2-\
                #      1/----->3
                # 3 needs 2 and 1; 2 needs 1
                #raise ValueError(f'Failed to resolve: depth-1 circular dependency in {vars_left}')
                pass

            if len(next_funcs) == 0:
                raise ValueError(f'Failed to resolve: no providers for {vars_left}')
            func_to_call = list(func_to_call)  + list(next_funcs)
            have_vars = tuple(set(vars_left) and set(have))
            try:
                return self._resolve_call(next_requires, have_vars, tuple(func_to_call))
            except RecursionLimit:
                print('before resolve')
                raise RuntimeError("Failed to resolve variables for call. "+
                                   f"Recursion limit of {RESOLVER_RECURSION_DEPTH} reached. "
                                   "This can happen if 1) there is no provider for a variable, "
                                   "2) you have circular dependencies or "
                                   "3) you have valid dependencies, but with depth larger than 15.")

    #-- API
    #---- Input

    def add_function(self, provides: Union[str, tuple] , requires=tuple(), cache=True):
        """ Decorator that registeres a variable provider. """
        if isinstance(provides, str):
            provides = [provides]

        if isinstance(requires, str):
            requires = [requires]

        def func_wrapper(user_function):
            if cache:
                func = self.cache_function(user_function)
            else:
                func = user_function
            # caching must preserve the signature
            self._register_provider(func, provides, requires)
            return func
        return func_wrapper

    def provider(self, user_function=None, *args, cache=True):
        """ Decorator that registeres a variable provider.

        Output variable name is the function name. If you want to use
            several output variables, use :meth:add_function
        Input variable names are the argument names
        """
        if user_function is not None:
            return self.provider(cache=cache)(user_function)
        else:
            def func_wrapper(user_function):
                provides = user_function.__name__
                requires = tuple(get_required_argnames(user_function))
                #print('provider requires', requires)
                return self.add_function(provides, requires, cache)(user_function)
            return func_wrapper

    #---- Output
    def dependency_graph(self):
        """ Return dependency graph of variables. """
        return dep_graph(self._function_requires, self._function_provides)

    def draw_dependency_graph(self, figsize=(8, 5), dpi=100, **kwargs):
        f = plt.figure(figsize=figsize, dpi=dpi)
        draw_dependency_graph(self.dependency_graph(), **kwargs)
        return f

    def _populate_call_kwd(self, f, current_blackboard):
        required = self._function_requires[f]
        # Apply function to blackboard
        call_kwd = {k: current_blackboard[k] for k in required}
        # -- pass optional parameters
        optional = get_optional_argnames(f)
        # print(f'{optional=} {current_blackboard=}')
        if len(optional):
            for o_ in optional:
                try:
                    call_kwd[o_] = current_blackboard[o_]
                except KeyError:
                    continue
        # print(f'{call_kwd=} {current_blackboard=}')
        return call_kwd

    def _update_blackboard(self, current_blackboard, f, retval):
        """
        Update the blackboard dict in-place.

        Args:
            current_blackboard (dict): blackboard dictionary
            f (callable): current function
            retval: value that function returned
                and is to be applied to blackboard

        """

        this_provides = self._function_provides[f]
        if isinstance(retval, dict):
            current_blackboard.update(retval)
        else:
            # Create dict to update current blackboard
            if len(this_provides)>1 and isinstance(retval, tuple):
                ret_len = len(retval)
            else:
                ret_len = 1
                retval = [retval]
            current_blackboard.update(
                {varname: val for varname, val in zip(this_provides, retval)}
            )
            if not len(this_provides) == ret_len:
                raise RuntimeWarning(f'Your function `{f.__name__}` returned {ret_len} values, but was registered to provide {this_provides}')

    def get_variables(self, varnames, **kwargs):
        funcs = self._resolve_call(need=tuple(varnames), have=tuple(kwargs.keys()))
        current_blackboard = kwargs
        for f in reversed(funcs):
            # Apply function to the blackboard
            call_kwd = self._populate_call_kwd(f, current_blackboard)
            retval = f(**call_kwd)
            # Unpack the response
            self._update_blackboard(current_blackboard, f, retval)
        return [current_blackboard[name] for name in varnames]

    def get_variables_no_call(self, varnames, no_call=[], **kwargs):
        """
        Get values for variables without calling cached functions.

        If the value is not in cache, return None

        This method is experimental.
        """

        funcs = self._resolve_call(need=tuple(varnames), have=tuple(kwargs.keys()))
        current_blackboard = kwargs
        for f in reversed(funcs):
            call_kwd = self._populate_call_kwd(f, current_blackboard)

            # -- Cache lookup 
            try:
                in_cache = self.cache.lookup(f, **call_kwd)
            except AttributeError:
                # f is probably just a function
                in_cache = True
            if in_cache:
                retval = f(**call_kwd)
            else:
                this_provides = self._function_provides[f]
                retval = tuple([None]*len(this_provides))
            #--

            self._update_blackboard(current_blackboard, f, retval)
            # Unpack the response
        return [current_blackboard[name] for name in varnames]

    def get_variable(self, varname, **kwargs):
        return self.get_variables([varname], **kwargs)[0]

    #------ Mappers

    def map_variables(self, varnames, **kwargs):
        return self.map(self.get_variables, varnames=[varnames], out_dim=len(varnames), **kwargs)

    def map_variables_no_call(self, varnames, **kwargs):
        return self.map(self.get_variables_no_call, varnames=[varnames], out_dim=len(varnames), **kwargs)

    def map_variable(self, varname, **kwargs):
        return self.map_variables([varname], **kwargs)[0]

    def map_variable_no_call(self, varname, **kwargs):
        return self.map_variables_no_call([varname], **kwargs)[0]

    def get_variables_xarray(self, varnames, **kwargs):
        """
        Return a xarray DataArray with mapped values

        If number of variables is >= 2, the 'varname' dimension
        has values for each variable

        """
        if isinstance(varnames, str):
            data = self.map_variable(varnames, **kwargs)
            outdim = 0
        else:
            data = self.map_variables(varnames, **kwargs)
            outdim = len(varnames)

        _dimcount = len(data.shape)
        print('_dimcount', _dimcount)
        _dimnames = list(kwargs.keys())
        dimvals = {k:kwargs[k] for k in _dimnames if len(kwargs[k]) > 1}
        if outdim:
            dimvals = {**{'varname': list(varnames)}, **dimvals}
        return lazy_imports.xarray.DataArray(
            data, dims=list(dimvals.keys()), coords=dimvals
        )



    #------ Plotting

    def plot_xarray(self, xar, **kwargs):
        """
        Plod data from xarray object
        """

        # Why, just why don't you preserve the order in coords??
        dims = {k:xar.coords[k].data for k in xar.dims}
        kwargs = {**kwargs, **dims}
        def safe_sel(*args, **kwargs):
            try:
                # the following line raises if we had None value
                return xar.sel(*args, **kwargs).__float__()
            except Exception:
                return None
        fig = self.plot2d(safe_sel, **kwargs)

        varnames = dims.get('varname', ('value', ))

        for ax, name in zip(fig.axes, varnames):
            ax.set_ylabel(name)
            ax.set_title(None)
        plt.tight_layout()
        return fig

    def plot_variables(self, varnames: Union[str, iter], **kwargs):
        if isinstance(varnames, str):
            varnames = (varnames, )
        fig = self.plot(self.get_variable, varname=varnames, **kwargs)
        for ax, name in zip(fig.axes, varnames):
            ax.set_ylabel(name)
            ax.set_title(None)
        plt.tight_layout()
        return fig

    def plot_variables2d(self, varnames: Union[str, iter], **kwargs):
        if isinstance(varnames, str):
            varnames = (varnames, )
        fig = self.plot2d(self.get_variable, varname=varnames, **kwargs)
        for ax, name in zip(fig.axes, varnames):
            ax.set_ylabel(name)
            ax.set_title(None)
        plt.tight_layout()
        return fig

    def plot_variables3d(self, varnames: Union[str, iter], **kwargs):
        if isinstance(varnames, str):
            varnames = (varnames, )
        fig = self.plot3d(self.get_variable, varname=varnames, **kwargs)
        return fig

    # lots of code duplication, but abstracting this would result in bad readability
    def plot_variables2d_no_call(self, varnames: Union[str, iter], **kwargs):
        if isinstance(varnames, str):
            varnames = [varnames]
        plt.ylabel(varnames[0])
        r = self.plot2d(self.get_variables_no_call, varnames=[varnames], **kwargs)
        return r

    def plot_variables3d_no_call(self, varnames: Union[str, iter], **kwargs):
        if isinstance(varnames, str):
            varnames = [varnames]
        r = self.plot3d(self.get_variables_no_call, varnames=[varnames], **kwargs)
        return r
