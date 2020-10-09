import inspect

def _maybe_unwrap(func):
    if hasattr(func, '__wrapped__'):
        return func.__wrapped__
    else:
        return func

def _defaults_len(spec):
    try:
        return len(spec.defaults)
    except (AttributeError, TypeError):
        return 0

def get_required_argnames(func):
    spec = inspect.getfullargspec(_maybe_unwrap(func))
    return spec.args[:-_defaults_len(spec)]

def get_optional_argnames(func):
    spec = inspect.getfullargspec(_maybe_unwrap(func))
    return spec.args[-_defaults_len(spec):] + spec.kwonlyargs
