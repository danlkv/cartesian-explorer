from cartesian_explorer import get_example_explorer
import numpy as np
import xarray
import matplotlib.pyplot as plt

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

