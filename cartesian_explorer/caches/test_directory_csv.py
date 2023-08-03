from cartesian_explorer.caches import DirectoryCSVCache
from pathlib import Path
import pickle
import pandas as pd

# TODO: test different ways of function declarations
# i.e. def foo(a=1) vs def foo(a)
def test_saving_format(tmp_path):
    cache = DirectoryCSVCache(tmp_path, verbose=1)
    calls = 0
    def foo(a=1):
        nonlocal calls 
        calls += 1
        return str(a)
    
    foo = cache.wrap(foo)
    a1 = foo(10)
    index_path = Path(tmp_path) / 'foo' / 'index.csv'
    df = pd.read_csv(index_path)
    assert len(df) == 1
    print(df)
    assert 'a' in df.columns
    assert 'foo' in df.columns

def test_csv_format(tmp_path):
    cache = DirectoryCSVCache(tmp_path, verbose=1)
    calls = 0
    def foo(a, b=1):
        nonlocal calls 
        calls += 1
        return str(a)
    
    foo = cache.wrap(foo)
    a1 = foo(10)
    foo(20)
    a2 = foo(10)
    a2 = foo(a=10)
    a2 = foo(a=10, b=1)
    a2 = foo(a=10, b=2)
    index_path = Path(tmp_path) / 'foo' / 'index.csv'
    df = pd.read_csv(index_path)
    assert len(df) == 3
    print(df)
    assert 'a' in df.columns
    assert 'b' in df.columns
    assert 'foo' in df.columns

    #   fname = df['foo'][10]
    #   hack_val = 'hack'
    #   with open(fname, 'wb') as f:
    #       pickle.dump(hack_val, f)
    #   assert foo(10) == hack_val
        
# this test is more end-to-end
def test_cache_works(tmp_path):
    cache = DirectoryCSVCache(tmp_path, verbose=1)
    calls = 0
    def foo(a=1):
        nonlocal calls 
        calls += 1
        return str(a), a+1
    
    foo = cache.wrap(foo)
    a1 = foo(10)
    foo(20)
    assert calls == 2, 'Cache is not calling on new argument; saving or lookup is broken'
    a2 = foo(10)
    assert a1 == a2, 'Cache returns incorrect vaules'
    assert calls == 2, 'Cache is not storing'
    cache.clear(foo)
    foo(10)
    assert calls == 3, 'Cache is not clearing'
