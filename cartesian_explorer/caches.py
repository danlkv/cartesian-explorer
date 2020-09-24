from cartesian_explorer.lib import lru_cache as cache1
from cartesian_explorer.lib import lru_cache_mproc as cache2

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
        sentinel = None
        key = cache1._make_key(args, kwargs, typed=False)
        val = func.cache_get(key, sentinel)
        print('lookup get', val)
        return (val is not sentinel)

    def clear(self, func):
        func.cache_clear()

    def info(self, func):
        func.cache_info()

class FunctoolsCache_Mproc(FunctoolsCache):
    def wrap(self, func, **kwargs) -> callable:
        return cache2.lru_cache(**kwargs)(func)

    def lookup(self, func, *args, **kwargs):
        sentinel = None
        key = cache2._make_key(args, kwargs, typed=False)
        val = func.cache_get(key, sentinel)
        print('lookup get', val)
        return (val is not sentinel)
