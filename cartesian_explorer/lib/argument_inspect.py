import inspect

def get_argnames(func):
    spec = inspect.getfullargspec(func)
    return spec.args + spec.kwonlyargs
