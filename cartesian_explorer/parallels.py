import multiprocessing as mproc
import multiprocessing.dummy as thrd
import joblib
from itertools import repeat

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
    def __init__(self, processes=2, *args, **kwargs):
        super().__init__(processes=processes)
        kwargs['n_jobs'] = kwargs.get('n_jobs', processes)
        self.par = joblib.Parallel(*args, **kwargs)

    def map(self, func, args):
        r = self.par(joblib.delayed(func)(x) for x in args)
        return r
