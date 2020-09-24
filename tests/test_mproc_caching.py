from cartesian_explorer import Explorer
from cartesian_explorer.caches import FunctoolsCache_Mproc
from cartesian_explorer import lru_cache_mproc

@lru_cache_mproc
def my_function(x):
    return x+1


def test_mproc_cache():
    explorer = Explorer(parallel='process', cache=FunctoolsCache_Mproc())
    data = explorer.map(my_function, processes=2, x=range(5))
    print('cache info', my_function.cache_info())
    print('cache', my_function._cache)
    data_no_call = explorer.map_no_call(my_function, x=range(2, 9))
    print(data, data_no_call)
    assert data_no_call[-1] is None
    assert data_no_call[-2] is None
    assert all(data_no_call[0:3] == data[2:])
