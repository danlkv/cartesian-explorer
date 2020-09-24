from cartesian_explorer import Explorer
from unittest.mock import MagicMock
import numpy as np

def test_caches():
    explorer = Explorer()
    mock = MagicMock()
    my_function = mock.my_function
    wrapped = explorer.cache_function(my_function)
    wrapped(a=1, b=2)
    wrapped(a=1, b=2)
    my_function.assert_called_once()
    my_function.assert_called_once_with(a=1, b=2)

def test_maps():
    explorer = Explorer()
    def my_function(x):
        return x+1
    data = explorer.map(my_function, x=range(5))
    print(data)
    assert np.allclose(data, np.arange(1,6))
