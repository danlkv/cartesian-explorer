import sys
import importlib

class LasyModule:
    def __init__(self, modulename):
        self.modulename = modulename
        self.module = None

    def __getattr__(self, attr):
        if self.module is None:
            try:
                self.module = importlib.import_module(self.modulename)
            except ImportError:
                print(f"LazyModule: {self.modulename} is missing.", file=sys.stderr)
                raise

        return self.module.__getattribute__(attr)

xarray = LasyModule('xarray')
diskcache = LasyModule('diskcache')
