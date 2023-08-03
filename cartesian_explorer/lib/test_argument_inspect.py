from cartesian_explorer.lib import argument_inspect
import pytest
import numpy as np

foo_args = ('a', )
foo_kwargs = {'b': 1, 'c': 'c'}
def foo(a, b=1, *args, c='c', **kwargs): #  type: ignore
    return

bar_args = tuple()
bar_kwargs = {}
def bar():
    return

functions_smoketest = [
    max,
    np.max,
    lambda x: x,
]

@pytest.mark.parametrize('function', functions_smoketest)
def test_funcdef_info_smoke(function):
    info = argument_inspect.FunctionDefInfo.from_function(function)
    assert type(info.args) == tuple
    assert type(info.kwargs) == dict

# TODO: test wrapped functions. E.g. with lru_cache.
#   Test functools.wraps
def test_funcdef_info_args():
    # -- All options
    info = argument_inspect.FunctionDefInfo.from_function(foo)
    assert info.args == foo_args
    assert info.kwargs == foo_kwargs
    assert info.accepts_varkw == True
    # -- No arguments
    info = argument_inspect.FunctionDefInfo.from_function(bar)
    assert info.args == bar_args
    assert info.kwargs == bar_kwargs
    assert info.accepts_varkw == False
    # -- All optional, funny names
    def bar2(a_1=1, bα=2, *args):
        pass
    info = argument_inspect.FunctionDefInfo.from_function(bar2)
    assert info.args == tuple()
    assert info.kwargs == { 'bα': 2, 'a_1': 1}
    assert info.accepts_varkw == False
    # -- Lambda
    baz = lambda x, y=1, **kwargs: 11
    info = argument_inspect.FunctionDefInfo.from_function(baz)
    assert info.args == ('x', )
    assert info.kwargs == { 'y': 1 }
    assert info.accepts_varkw == True
