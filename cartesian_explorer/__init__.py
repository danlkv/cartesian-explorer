__version__ = '0.1.5'
import logging
mpl_logger = logging.getLogger('matplotlib')
mpl_logger.setLevel(logging.WARNING)

from cartesian_explorer.lib.lru_cache import lru_cache
from cartesian_explorer.lib.lru_cache_mproc import lru_cache as lru_cache_mproc
from cartesian_explorer.lib.dict_product import dict_product
from cartesian_explorer.Explorer import Explorer

