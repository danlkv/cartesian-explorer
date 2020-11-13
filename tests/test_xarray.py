from cartesian_explorer import get_example_explorer
import numpy as np

def test_xarray_out():

    ex = get_example_explorer()

    xar = ex.get_variables_xarray("Mass", isotope=["Pb187", "Pb186"], time_sec=np.linspace(0, 10, 100))

    assert xar.shape == (2, 100)
    assert xar.dims == ('isotope', 'time_sec')

    xar = ex.get_variables_xarray(("Mass", "Speed"), isotope=["Pb187", "Pb186"], time_sec=np.linspace(0, 10, 100))

    assert xar.shape == (2, 2, 100)
    assert xar.dims == ('varname', 'isotope', 'time_sec')

