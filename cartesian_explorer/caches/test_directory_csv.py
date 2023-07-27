from cartesian_explorer.caches import DirectoryCSVCache
from pathlib import Path
import pickle
import pandas as pd

def test_directory_csv_cache(tmp_path):
    cache = DirectoryCSVCache(tmp_path, verbose=1)
    calls = 0
    def foo(a=1):
        nonlocal calls 
        calls += 1
        return str(a)
    
    foo = cache.wrap(foo)
    a1 = foo(10)
    foo(20)
    a2 = foo(10)
    assert a1 == a2
    assert calls == 2
    index_path = Path(tmp_path) / 'foo' / 'index.csv'
    df = pd.read_csv(index_path, index_col='0')
    assert len(df) == 2

    #   fname = df['foo'][10]
    #   hack_val = 'hack'
    #   with open(fname, 'wb') as f:
    #       pickle.dump(hack_val, f)
    #   assert foo(10) == hack_val


        
