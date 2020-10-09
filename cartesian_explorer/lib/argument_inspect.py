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

def _last_n_slice(n):
    # :double facepalm:
    # just WHY can't you make l[-0:] work as expected???
    if n:
        return slice(-n, None)
    else:
        return slice(None, 0)

def _except_last_n_slice(n):
    # :double facepalm:
    # just WHY can't you make l[:-0] work as expected???
    return slice(None, (-n or None))

def get_required_argnames(func):
    spec = inspect.getfullargspec(_maybe_unwrap(func))
    return spec.args[_except_last_n_slice(_defaults_len(spec))]

def get_optional_argnames(func):
    spec = inspect.getfullargspec(_maybe_unwrap(func))
    return spec.args[_last_n_slice(_defaults_len(spec))] + spec.kwonlyargs
