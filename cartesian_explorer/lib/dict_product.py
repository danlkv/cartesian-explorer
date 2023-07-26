from collections.abc import Iterable
from typing import Any
import itertools

def dict_product(**kwargs):
    keys = kwargs.keys()
    vals = kwargs.values()
    for instance in itertools.product(*vals):
        yield dict(zip(keys, instance))

def index_newdim(index_iter: Iterable[dict], **kwargs: Any):
    """
    Expand list of named indices `index_iter` with dimension values in `**kwargs`.

    Values and their order in `index_iter` take precedence.
    """
    if len(kwargs) == 0:
        yield from index_iter

    for index_val in index_iter:
        # Note: { **kwargs, **index_val } will not preserve order
        newdict = { **index_val }
        for key, val in kwargs.items():
            if key in newdict:
                continue
            newdict[key] = val
        yield newdict
