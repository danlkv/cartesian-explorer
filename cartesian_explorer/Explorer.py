from cartesian_explorer.ExplorerBasic import ExplorerBasic
from typing import Union
from functools import update_wrapper
from itertools import repeat

def limit_recurse(limit=10):
    def limit_wrapper(func):
        ncalls = 0
        def wrapper(*args, **kwargs):
            nonlocal ncalls
            ncalls += 1
            if ncalls > limit:
                ncalls = 0
                raise RuntimeError(f"Recursion limit of {limit} exceeded")
            ret = func(*args, **kwargs)
            ncalls = 0
            return ret
        update_wrapper(wrapper, func)
        return wrapper
    return limit_wrapper

class Explorer(ExplorerBasic):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._variable_providers = {}
        self._function_requires = {}
        self._function_provides = {}

    def _register_provider(self, func, provides, requires):
        for var in provides:
            self._variable_providers[var] = func
        self._function_provides[func] = list(provides)
        self._function_requires[func] = list(requires)

    def _resolve_1(self, requires):
        funcs_to_call = []
        for var in requires:
            try:
                var_provider = self._variable_providers[var]
            except KeyError:
                continue

            funcs_to_call.append(var_provider)

        next_requires = sum([self._function_requires[func] for func in funcs_to_call], [])
        #print('fu', funcs_to_call)
        return tuple(set(funcs_to_call)), tuple(set(next_requires))

    @limit_recurse(limit=10)
    def _resolve_call(self, need, have, func_to_call=[]):
        have = set(have)
        vars_left = set(need) - set(have)
        #print('resolving', need, 'have', have, 'left', vars_left)
        if len(vars_left)==0:
            return func_to_call
        else:
            next_funcs, next_requires = self._resolve_1(vars_left)
            #print('next', next_funcs, next_requires)
            if any(x in vars_left for x in next_requires):
                raise ValueError('Failed to resolve: depth-1 circular dependency')
            if len(next_funcs) == 0:
                raise ValueError(f'Failed to resolve: no providers for {vars_left}')
            func_to_call = list(func_to_call)  + list(next_funcs)
            have_vars = tuple(set(vars_left) and set(have))
            return self._resolve_call(next_requires, have_vars, func_to_call)

    #-- API
    #---- Input

    def add_function(self, provides: Union[str, tuple] , requires=tuple()):
        if isinstance(provides, str):
            provides = [provides]

        if isinstance(requires, str):
            requires = [requires]

        def func_wrapper(user_function):
            func = self.cache_function(user_function)
            self._register_provider(func, provides, requires)
            return func
        return func_wrapper

    #---- Output

    def get_variables(self, varnames, **kwargs):
        funcs = self._resolve_call(need=varnames, have=list(kwargs.keys()))
        current_blackboard = kwargs
        for f in reversed(funcs):
            required = self._function_requires[f]
            # Apply function to blackboard
            call_kwd = {k: current_blackboard[k] for k in required}
            retval = f(**call_kwd)
            # Unpack the response
            if isinstance(retval, dict):
                current_blackboard.update(retval)
            else:
                # Create dict to update current blackboard
                this_provides = self._function_provides[f]
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
        return [current_blackboard[name] for name in varnames]

    def get_variable(self, varname, **kwargs):
        return self.get_variables([varname], **kwargs)[0]

    #------ Mappers
    def map_variables(self, varnames, **kwargs):
        return self.map(self.get_variables, varnames=[varnames], **kwargs)

    def map_variables_no_call(self, varnames, **kwargs):
        return self.map_no_call(self.get_variables, varnames=[varnames], **kwargs)

    def map_variable(self, varname, **kwargs):
        return self.map_variables([varname], **kwargs)[0]

    def map_variable_no_call(self, varname, **kwargs):
        return self.map_variables_no_call([varname], **kwargs)[0]

    #------ Plotting
    def plot_variables2d(self, varnames: Union[str, iter], **kwargs):
        if isinstance(varnames, str):
            varnames = [varnames]
        return self.plot2d(self.get_variables, varnames=[varnames], **kwargs)

    def plot_variables3d(self, varnames: Union[str, iter], **kwargs):
        if isinstance(varnames, str):
            varnames = [varnames]
        return self.plot3d(self.get_variables, varnames=[varnames], **kwargs)
