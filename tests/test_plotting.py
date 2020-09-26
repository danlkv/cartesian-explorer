from cartesian_explorer import Explorer
import numpy as np
import matplotlib.pyplot as plt

SHOW_PLOTS = False

def maybe_show_plots():
    if SHOW_PLOTS:
        try:
            plt.show()
        except Exception:
            pass

def my_function(x):
    return np.sin(x/10)

def test_plot2d():
    explorer = Explorer()
    explorer.plot2d(my_function, x=range(50))
    ax = plt.gca()
    assert ax.xaxis.get_label().get_text() == 'x'
    assert len(ax.lines) == 1
    line = ax.lines[0]
    assert all(line.get_xdata() == np.arange(0, 50))
    assert all(line.get_ydata() == my_function(np.arange(0, 50)))
    maybe_show_plots()

def my_function2d(re, im):
    return np.sin((re +1j*im)/10)

def test_plot3d():
    explorer = Explorer()
    explorer.plot3d(my_function2d, im=range(-10, 10), re=range(70) )
    ax = plt.gca()
    assert ax.xaxis.get_label().get_text() == 're'
    assert ax.yaxis.get_label().get_text() == 'im'
    maybe_show_plots()
