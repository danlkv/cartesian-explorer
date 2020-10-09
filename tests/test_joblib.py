from unittest.mock import MagicMock
import time

from cartesian_explorer import Explorer
from cartesian_explorer.caches import JobLibCache
from cartesian_explorer.parallels import JobLib


def test_caches(tmpdir):
    """ Tests if cache indeed caches."""
    cache = JobLibCache(str(tmpdir), verbose=1)
    explorer = Explorer(cache=cache)
    calls = 0
    @cache
    def my_function(a, b):
        nonlocal calls
        calls += 1
        return a+b+1
    wrapped = explorer.cache_function(my_function)
    print('wrapped', wrapped)
    wrapped(a=1, b=2)
    wrapped(a=1, b=2)
    assert calls == 1

def test_works_with_cache(tmpdir):
    """ Tests if the cache properly wraps functions to allow inspection."""
    cache = JobLibCache(str(tmpdir), verbose=1)
    explorer = Explorer(cache=cache)
    @explorer.provider
    def c(a, b=1):
        return a + b
    z = explorer.get_variable('c', a=2)
    assert z == 2 + 1

    z = explorer.get_variable('c', a=2, b=2)
    assert z == 2 + 2


# Does not work for .3
DELAY = .5
def my_function(x):
    time.sleep(DELAY)
    return x+1

def test_mproc_cache(tmpdir):
    cache = JobLibCache(str(tmpdir), verbose=1)
    # smoke
    explorer = Explorer(parallel='joblib', cache=cache)
    parallel = JobLib(n_jobs=3, verbose=10)

    explorer = Explorer(parallel=parallel, cache=cache)
    func = explorer.cache_function(my_function)

    start = time.time()
    data = explorer.map(func, processes=2, x=range(6))
    dur = time.time() - start
    assert dur < 6*DELAY

    data_no_call = explorer.map_no_call(func, x=range(3, 10))
    print(data, data_no_call)
    assert data_no_call[-1] is None
    assert data_no_call[-2] is None
    assert all(data_no_call[0:3] == data[3:])
