__version__ = '0.1.11'
import logging
mpl_logger = logging.getLogger('matplotlib')
mpl_logger.setLevel(logging.WARNING)

from cartesian_explorer import lazy_imports

from cartesian_explorer.lib.lru_cache import lru_cache
from cartesian_explorer.lib.lru_cache_mproc import lru_cache as lru_cache_mproc
from cartesian_explorer.lib.dict_product import dict_product
from cartesian_explorer.Explorer import Explorer

def get_example_explorer():
    """ Create a demonstrative explorer.

    The explorer describes radioactve decay
    of Pb isotopes.

    Provides:
        Mass: mass left of isotope of type `isotope`
        Speed: curernt speed of decay at `time_sec`

    Requires:
        time_sec: time to calculate outputs at.
        isotope: type of isotope: one of "Pb186", "Pb187", "Pb188"

    """
    import numpy as np
    ex = Explorer()
    @ex.provider
    @ex.add_function(provides='Mass', requires=('time_sec', 'T'))
    def mass(time_sec, T):
        return np.exp(-T*time_sec)

    @ex.add_function(provides='Speed', requires=('time_sec', 'T'))
    def speed(time_sec, T):
        return -T*np.exp(-T*time_sec)

    @ex.provider
    def T(isotope):
        if isotope == 'Pb186':
            return np.log(2)/4.82
        if isotope == 'Pb187':
            return np.log(2)/15.2
        if isotope == 'Pb188':
            return np.log(2)/35.2
    return ex
