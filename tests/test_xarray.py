from cartesian_explorer import get_example_explorer
from cartesian_explorer.ExplorerBasic import ExplorerBasic
from cartesian_explorer import dict_product
import numpy as np
import xarray
import matplotlib.pyplot as plt

# -- Testing mapping interface

def test_map_commutes_with_slice():
    """
    The idea of this test is to check that merging output from `map` works as expected

    For mapping function :math:`M`, ``xarray`` slices :math:`s_i` and data :math:`D`, 

    .. math::

        \sum_i M(D, s_i) = M(D, \sum_i s_i)
    
    where the summation represents ``xarray.combine_by_coords`` in the first case
    and concatenation of slices in the second.

    The reason I use ``combine_by_coords`` is that it seems to to be the closest to
    complementary operation of ``DataArray.sel``

    """
    ex = ExplorerBasic()
    M = ex.map_xarray
    def sum_slices(s_arr):
        result = {}
        for other in s_arr:
            for k in other:
                l = result.get(k, [])
                result[k] = list(set(l + other[k]))
        return result
    
    def sum_data(d_arr):
        return xarray.combine_by_coords(d_arr)

    # -- metatest: test that add is complementary to slice
    arr = xarray.DataArray(np.random.randn(2,2), coords=dict(a=[0,1], b=[2,3]))
    slices = [dict(a=[0,1], b=[2]), dict(a=[0, 1], b=[3])]
    slice_arrs = [arr.sel(s) for s in slices]
    S = sum_slices(slices)
    D = arr.sel(S)
    assert D.equals(sum_data(slice_arrs))

    # -- test slicing using array
    arr = xarray.DataArray(np.random.randn(2,2), coords=dict(a=[0,1], b=[2,3]))
    slices = [dict(a=[0,1], b=[2]), dict(a=[0, 1], b=[3])]
    S = sum_slices(slices)
    K1 = sum_data([M(D.sel, **sl) for sl in slices])
    K2 = M(D.sel, **sum_slices(slices))
    assert K1.equals(K2)

    # -- test slicing using constants
    arr = xarray.DataArray(np.random.randn(2,2), coords=dict(a=[0,1], b=[2,3]))
    constants = [dict(a=0), dict(a=1)]
    variables = [dict(b=[2, 3]), dict(b=[2, 3])]
    S = dict(a=[0, 1], b=[2, 3])
    data_arr = [M(D.sel, variables=v, constants=c) for
                v, c in zip(variables, constants)
                ]
    data_arr_xarray = [
        D.sel(**v, **c) for v, c in zip(variables, constants)
    ]
    for a1, a2 in zip(data_arr, data_arr_xarray):
        assert a1.equals(a2)


# -- Testing Explorer

def test_xarray_out():

    ex = get_example_explorer()

    xar = ex.get_variables_xarray("Mass", isotope=["Pb187", "Pb186"], time_sec=np.linspace(0, 10, 100))

    assert xar.shape == (2, 100)
    assert xar.dims == ('isotope', 'time_sec')

    xar = ex.get_variables_xarray(("Mass", "Speed"), isotope=["Pb187", "Pb186"], time_sec=np.linspace(0, 10, 100))

    assert xar.shape == (2, 2, 100)
    assert xar.dims == ('varname', 'isotope', 'time_sec')

def test_xarray_readwrite(tmp_path):

    ex = get_example_explorer()

    xar = ex.get_variables_xarray(("Mass", "Speed"), isotope=["Pb187", "Pb186"], time_sec=np.linspace(0, 10, 100))

    tmp_file = tmp_path / 'caex_test.nc'
    xar.to_netcdf(tmp_file)

    rxar = xarray.load_dataarray(tmp_file)
    assert rxar.shape == (2, 2, 100)
    assert rxar.dims == ('varname', 'isotope', 'time_sec')
    # Why, just why don't you preserve the order in coords??
    dims = {k:rxar.coords[k] for k in rxar.dims}

    vals = ex.map(rxar.sel, **dims)
    assert vals.shape == (2, 2, 100)


    fig = ex.plot_xarray(rxar)
    axes = fig.axes
    assert len(axes) == 2
    assert len(axes[0].lines) == 2
    assert len(axes[1].lines) == 2
    assert len(axes[1].lines[0].get_xdata()) == 100
    xvals = axes[1].lines[0].get_xdata() 

    assert np.allclose(xvals, np.linspace(0, 10, 100))

