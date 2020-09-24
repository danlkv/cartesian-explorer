from cartesian_explorer.lib import lru_cache as cache1

class CacheIFC:
    def wrap(self, func, **kwargs) -> callable:
        raise NotImplementedError

    def call(func, *args, **kwargs):
        raise NotImplementedError

    def lookup(self, func, *args, **kwargs):
        raise NotImplementedError

    def clear(self, func):
        raise NotImplementedError


class FunctoolsCache(CacheIFC):
    def wrap(self, func, **kwargs) -> callable:
        return cache1.lru_cache(**kwargs)(func)

    def call(func, *args, **kwargs):
        return func(*args, **kwargs)

    def lookup(self, func, *args, **kwargs):
        sentinel = object()
        key = cache1._make_key(args, kwargs, tyyped=False)
        val = func.cache_get(key, sentinel)
        return (val is not sentinel)

    def clear(self, func):
        func.cache_clear()

    def info(self, func):
        func.cache_info()
