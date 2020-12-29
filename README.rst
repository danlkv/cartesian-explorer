==================
Cartesian Explorer
==================


.. image:: https://img.shields.io/pypi/v/cartesian-explorer.svg
        :target: https://pypi.python.org/pypi/cartesian-explorer

.. image:: https://github.com/danlkv/cartesian-explorer/workflows/Test/badge.svg
        :target: https://github.com/danlkv/cartesian-explorer/actions?query=workflow%3ATest
        
        
.. image:: https://readthedocs.org/projects/cartesian-explorer/badge/?version=latest
        :target: https://cartesian-explorer.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


A handy tool to map functions over their domains.



Works:

- Map over cartesian product of arguments: pass arrays of values for function argument
- Built-in caching
- Handy plotting utilities
- Resolving dependencies between functions that require and provide variables

Usage
-----

Map

.. code-block:: python 

    from cartesian_explorer import Explorer

    explorer = Explorer()

    def my_function(x, y):
        return x+y
    data = explorer.map(my_function, x=range(5), y=range(3))
    print(data)
    assert data.shape == (5, 3)
    assert data[1, 2] == my_function(1, 2)


Cache

.. code-block:: python

    from cartesian_explorer import Explorer
    explorer = Explorer()
    mock = MagicMock()
    my_function = mock.my_function
    wrapped = explorer.cache_function(my_function)
    wrapped(a=1, b=2)
    wrapped(a=1, b=2)
    my_function.assert_called_once_with(a=1, b=2)


TODO
----

- [ ] Interpolation, extrapolation
- [ ] Vectorized providers
- [x] Plot distribution props along additional distribution var
- 
