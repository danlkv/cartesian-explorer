import numpy as np
from multiprocessing import Pool
import time
from math import sin, cos, radians

def user_func_io(a):
    print('called userfunc')
    time.sleep(1)
    return a+1

def user_func_cpu(a):
    """ Multiplies 1 by sin^2 + cos^2 for all angles """
    print('userfunc cpu')
    product = 1.0
    start = time.time()
    for counter in range(1, 10000, 1):
        for dex in list(range(1, 360, 1)):
            angle = radians(dex)
            product *= sin(angle)**2 + cos(angle)**2
    end = time.time()
    print('userfunc time:', end - start)
    return product + a

def test_ordinary_array_io():
    arr = np.empty((10, ))
    start = time.time()
    with Pool(processes=4) as pool:
        arr[:] = pool.map(user_func_io, range(10))
    end = time.time()
    assert np.allclose(arr , np.arange(10) + 1)
    print(f"total time: {end - start}")
    print('arr', arr)

def test_ordinary_array_cpu():
    arr = np.empty((10, ))
    start = time.time()
    with Pool(processes=4) as pool:
        arr[:] = pool.map(user_func_cpu, range(10))
    end = time.time()
    print(f"total time: {end - start}")
    print(arr)

def test_list_cpu():
    arr = []
    start = time.time()
    with Pool(processes=4) as pool:
        arr[:] = pool.map(user_func_cpu, range(10))
    end = time.time()
    print(f"total time: {end - start}")
    print(arr)

if __name__ == "__main__":
    test_ordinary_array_io()
    test_ordinary_array_cpu()
