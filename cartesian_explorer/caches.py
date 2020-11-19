from cartesian_explorer.lib import lru_cache as cache1
from cartesian_explorer.lib import lru_cache_mproc as cache2
from cartesian_explorer.lib import lru_cache_diskcache as cache_disk

import joblib

class CacheIFC:
    def __call__(self, func, **kwargs):
        cached = self.wrap(func, **kwargs)
        cached._original = func
        return cached

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

    def lookup(self, func, *args, **kwargs):
        sentinel = None
        key = cache1._make_key(args, kwargs, typed=False)
        val = func.cache_get(key, sentinel)
        return (val is not sentinel)

    def call(func, *args, **kwargs):
        return func(*args, **kwargs)

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

class FunctoolsCache_Disk(FunctoolsCache):
    def __init__(self, directory):
        self.directory = directory

    def wrap(self, func, **kwargs) -> callable:
        kwargs['directory'] = self.directory
        return cache_disk.lru_cache(**kwargs)(func)

    def lookup(self, func, *args, **kwargs):
        sentinel = None
        key = cache_disk._make_key(args, kwargs, typed=False)
        val = func.cache_get(key, sentinel)
        print('lookup get', val)
        return (val is not sentinel)

class JobLibCache(CacheIFC):
    def __init__(self, cachedir, verbose=0):
        self.memory = joblib.Memory(cachedir, verbose=verbose)

    def wrap(self, func, **kwargs) -> callable:
        return self.memory.cache(func)

    def call(self, func, *args, **kwargs):
        return func(*args, **kwargs)

    def lookup(self, func, *args, **kwargs):
        """
        They didn't merge it yet, but hope this works

https://github.com/joblib/joblib/pull/820/files#diff-c66af844ce2989eb95b416d643de531d
        """
        func_id, args_id = func._get_output_identifiers(*args, **kwargs)
        return func.store_backend.contains_item((func_id, args_id))

    def clear(self, func):
        func.clear()
