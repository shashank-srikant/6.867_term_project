#!/usr/bin/env python3

from bayes_opt import BayesianOptimization
from bayes_opt import UtilityFunction
import numpy as np
import random

import matplotlib.pyplot as plt
from matplotlib import gridspec

import functools

kappa = 5

observed = {
    0: 1.52,
    1: 1.51,
    2: 1.63,
    3: 1.81,
    4: 2.03,
    5: 2.62,
    6: 60.40,
    7: 9317032.63,
    8: 54501934340.98,
    9: 950553104447.76,
    10: 1432370346851.65,
}

observed = {k: 1/np.log(v) for (k, v) in observed.items() if v is not None}

def function(**kwargs):
    x = kwargs['x']
    x = int(round(x))

    return observed[x]

optimizer = BayesianOptimization(
    function,
    {'x': (0, 10)},
    random_state=1,
)
utility_function = UtilityFunction(kind="ucb", kappa=kappa, xi=0)
x = np.linspace(0, 10, 10000).reshape(-1, 1)
x_int = np.arange(0, 11).reshape(-1, 1)

def posterior(optimizer, x_obs, y_obs, grid):
    optimizer._gp.fit(x_obs, y_obs)

    mu, sigma = optimizer._gp.predict(grid, return_std=True)
    return mu, sigma

def plot_gp(optimizer, x, y):
    fig = plt.figure(figsize=(16, 10))
    steps = len(optimizer.space)

    fig.suptitle(
        'Gaussian Process and Utility Function After {} Steps'.format(steps),
        size=32,
    )
    plt.rcParams.update({'font.size': 16})
    gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1])
    axis = plt.subplot(gs[0])
    acq = plt.subplot(gs[1])

    x_obs = np.array([[res["params"]["x"]] for res in optimizer.res])
    y_obs = np.array([res["target"] for res in optimizer.res])

    mu, sigma = posterior(optimizer, x_obs, y_obs, x)
    if y is not None:
        axis.plot(x, y, linewidth=3, label='Target')
    axis.plot(x_obs.flatten(), y_obs, 'D', markersize=14, label=u'Observations', color='r')
    axis.plot(x, mu, '--', color='k', label='Prediction')

    axis.fill(np.concatenate([x, x[::-1]]),
              np.concatenate([mu - 1.9600 * sigma, (mu + 1.9600 * sigma)[::-1]]),
        alpha=.6, fc='c', ec='None', label='95% confidence interval')

    axis.set_xlim((0, 10))
    axis.set_ylim((None, None))
    axis.set_ylabel('1/log(loss)', fontdict={'size':20})

    utility = utility_function.utility(x, optimizer._gp, 0)
    utility_int = utility_function.utility(x_int, optimizer._gp, 0)

    acq.plot(x, utility, label='Utility Function', color='purple')
    acq.plot(x_int[np.argmax(utility_int)], np.max(utility_int), '*', markersize=24,
             label=u'Next Best Guess', markerfacecolor='gold', markeredgecolor='k', markeredgewidth=1)
    acq.set_xlim((0, 10))
    acq.set_ylim((0, np.max(utility) + 0.5))
    acq.set_ylabel('Utility', fontdict={'size':20})

    axis.set_xlabel('NIter', fontdict={'size':20})
    acq.set_xlabel('NIter', fontdict={'size':20})

    axis.legend(loc=1, borderaxespad=0.)
    acq.legend(loc=1, borderaxespad=0.)

    fig.tight_layout(rect=[0, 0.03, 1, 0.95])

def refit():
    x_obs = np.array([[res["params"]["x"]] for res in optimizer.res])
    y_obs = np.array([res["target"] for res in optimizer.res])
    optimizer._gp.fit(x_obs, y_obs)

optimizer.probe({'x': 5}, lazy=False)

prev_probe = None
next_probe = 5
while prev_probe != next_probe:
    refit()
    if prev_probe == 1:
        plot_gp(optimizer, x, y=None)
        plt.show()
    refit()
    utility_int = utility_function.utility(x_int, optimizer._gp, 0)
    prev_probe = next_probe
    next_probe = np.argmax(utility_int)
    optimizer.probe({'x': next_probe}, lazy=False)
