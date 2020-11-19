import multiprocessing as mproc
import logging
import multiprocessing.dummy as thrd
import joblib
from itertools import repeat
import importlib
class LazyModule:
    def __init__(self, module_name):
        self.module = None
        self.module_name = module_name

    def __getattr__(self, prop):
        if self.module is None:
            self.module = importlib.import_module(self.module_name)
        return self.module.__getattribute__(prop)

ray = LazyModule('ray')

def apply_kwargs(pair):
    func, kwargs = pair
    return func(**kwargs)

def apply_args(pair):
    func, args = pair
    return func(*args)

class ParallelIFC:
    def __init__(self, processes=2):
        self.processes = processes

    def map(self, func, args):
        raise NotImplementedError

    def starmap(self, func, args):
        return self.map(apply_args, zip(repeat(func), args))

    def starstarmap(self, func, args):
        return self.map(apply_kwargs, zip(repeat(func), args))

class Multiprocess(ParallelIFC):
    def map(self, func, args):
        with mproc.Pool(processes=self.processes) as pool:
            return pool.map(func, args)

class Thread(ParallelIFC):
    def map(self, func, args):
        with thrd.Pool(processes=self.processes) as pool:
            return pool.map(func, args)

class JobLib(ParallelIFC):
    def __init__(self, processes=None, *args, **kwargs):
        super().__init__(processes=processes)
        if processes:
            kwargs['n_jobs'] = kwargs.get('n_jobs', processes)
        self.par = joblib.Parallel(*args, **kwargs)

    def map(self, func, args):
        r = self.par(joblib.delayed(func)(x) for x in args)
        return r

class Ray(ParallelIFC):
    def __init__(self, processes=None, *args, **kwargs):
        super().__init__(processes=processes)
        kwargs['ignore_reinit_error'] = kwargs.get('ignore_reinit_error', True)
        kwargs['log_to_driver'] = kwargs.get('log_to_driver', False)
        if processes:
            kwargs['num_cpus'] = kwargs.get('num_cpus', processes)
        ray.init(*args, **kwargs)

    def map(self, func, args):
        func = ray.remote(func)
        r = [func.remote(x) for x in args]
        return ray.get(r)
