import numpy as np
import matplotlib.pyplot as plt
from cartesian_explorer import CAEX_PLOT_KWG

def with_std(x, line_data, **plot_kwargs):
    line_data = line_data.astype(np.float64)
    maximums = np.nanmax(line_data, axis=-1)
    minimums = np.nanmin(line_data, axis=-1)

    std = np.nanstd(line_data, axis=-1)
    mean = np.nanmean(line_data, axis=-1)
    # --
    # call the plotting function
    fill_kwargs = dict(
        alpha=plot_kwargs.get('band_alpha', 0.05), color=plot_kwargs.get('color')
    )
    [plot_kwargs.pop(x, None) for x in CAEX_PLOT_KWG]
    plt.plot(x, mean, **plot_kwargs)
    #plt.fill_between(x, minimums, maximums, **fill_kwargs)
    #plot_func(x, minimums, alpha=0.3, **line_local_plot_kwargs)
    #plot_func(x, maximums, alpha=0.3, **line_local_plot_kwargs)
    plt.fill_between(x, mean-2*std, mean+2*std, **fill_kwargs)

def with_range(x, line_data, **plot_kwargs):
    line_data = line_data.astype(np.float64)
    maximums = np.nanmax(line_data, axis=-1)
    minimums = np.nanmin(line_data, axis=-1)

    mean = np.nanmean(line_data, axis=-1)
    # --
    # call the plotting function
    fill_kwargs = dict(
        alpha=plot_kwargs.get('band_alpha', 0.05), color=plot_kwargs.get('color')
    )
    [plot_kwargs.pop(x, None) for x in CAEX_PLOT_KWG]
    plt.plot(x, mean, **plot_kwargs)
    plt.fill_between(x, minimums, maximums, **fill_kwargs)

def log_std(x, line_data, sigma_interval=2, **plot_kwargs):
    """
    1. Plotting errors on log-plot is a bit tricky.

    In short, using log base e
        z = log(y)
        dz = d(log(y)) = dy/y

    See this for more details:

        https://faculty.washington.edu/stuve/log_error.pdf

    2. Means on log plot are not so easy as well.
    Chanses are, if you are plotting something with distribution
    on log plot, you expect the distribution to be
    _logarithmically normal_

    Hense, the mean should be the _geometric mean_

    See here, page 9:

    https://s3.amazonaws.com/cdn.graphpad.com/faq/1910/file/1487logaxes.pdf

    """

    line_data = line_data.astype(np.float64)
    plt.yscale('log')

    gmean = np.exp(np.nanmean(np.log(line_data), axis=-1))
    dz = np.nanstd(np.log(line_data), axis=-1)
    dmean = np.exp(sigma_interval*dz)
    # --
    # call the plotting function
    fill_kwargs = dict(
        alpha=plot_kwargs.get('band_alpha', 0.05), color=plot_kwargs.get('color')
    )
    [plot_kwargs.pop(x, None) for x in CAEX_PLOT_KWG]
    plt.plot(x, gmean, **plot_kwargs)
    plt.fill_between(x, gmean*dmean, gmean/dmean, **fill_kwargs)
