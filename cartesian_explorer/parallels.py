from __future__ import annotations
import multiprocessing as mproc
import logging
import multiprocessing.dummy as thrd
import joblib
from itertools import repeat
import importlib

# -- Lazy imports

class LazyModule:
    def __init__(self, module_name):
        self.module = None
        self.module_name = module_name

    def __getattr__(self, prop):
        if self.module is None:
            self.module = importlib.import_module(self.module_name)
        return self.module.__getattribute__(prop)

ray = LazyModule('ray')
# --

def get_available_parallel():
    subclasses = ParallelIFC.__subclasses__()
    return [cls.string_label for cls in subclasses]

def get_parallel(parallel: str | None, processes: int | None = None):
    subclasses = ParallelIFC.__subclasses__()
    if parallel is None:
        parallel = 'process'
    
    for cls in subclasses:
        if cls.string_label == parallel:
            return cls(processes=processes)
    raise ValueError(f'Unknown parallel {parallel}. Available: {get_available_parallel()}')


def apply_kwargs(pair):
    func, kwargs = pair
    return func(**kwargs)

def apply_args(pair):
    func, args = pair
    return func(*args)

class ParallelIFC:
    processes: int | None
    string_label: str

    def __init__(self, processes: int | None = None):
        self.processes = processes

    def map(self, func, args):
        raise NotImplementedError

    def starmap(self, func, args):
        return self.map(apply_args, zip(repeat(func), args))

    def starstarmap(self, func, args):
        return self.map(apply_kwargs, zip(repeat(func), args))

class Multiprocess(ParallelIFC):
    string_label = 'process'
    def map(self, func, args):
        with mproc.Pool(processes=self.processes) as pool:
            return pool.map(func, args)

class Thread(ParallelIFC):
    string_label = 'thread'
    def map(self, func, args):
        with thrd.Pool(processes=self.processes) as pool:
            return pool.map(func, args)

class JobLib(ParallelIFC):
    string_label = 'joblib'
    def __init__(self, processes=None, *args, **kwargs):
        super().__init__(processes=processes)
        if processes:
            kwargs['n_jobs'] = kwargs.get('n_jobs', processes)
        self.par = joblib.Parallel(*args, **kwargs)

    def map(self, func, args):
        r = self.par(joblib.delayed(func)(x) for x in args)
        return r

class Ray(ParallelIFC):
    string_label = 'ray'
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
