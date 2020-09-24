from cartesian_explorer.ExplorerBasic import ExplorerBasic

class Explorer(ExplorerBasic):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._variable_providers = {}
        self._function_requires = {}

    def _register_provider(self, func, provides, requires):
        for var in provides:
            self._variable_providers[var] = func
        self._function_requires[func] = requires

    #-- API
    #---- Input

    def add_function(self, provides: tuple, requires=tuple()):
        def func_wrapper(user_function):
            func = self.cache_function(user_function)
            self._register_provider(func, provides, requires)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper
        return func_wrapper

