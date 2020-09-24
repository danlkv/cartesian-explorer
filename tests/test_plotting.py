from cartesian_explorer import Explorer
import numpy as np
import matplotlib.pyplot as plt


def my_function(x):
    return np.sin(x/10)

def test_mproc():
    explorer = Explorer()
    explorer.plot2d(my_function, x=range(50))
    ax = plt.gca()
    assert ax.xaxis.get_label().get_text() == 'x'
    assert len(ax.lines) == 1
    line = ax.lines[0]
    assert all(line.get_xdata() == np.arange(0, 50))
    assert all(line.get_ydata() == my_function(np.arange(0, 50)))
    try:
        plt.show()
    except Exception:
        print('No screen!')
