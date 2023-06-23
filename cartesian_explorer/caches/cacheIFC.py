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

