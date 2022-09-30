#!/usr/bin/env python3

import numpy as np
import scipy as sp
import matplotlib.pyplot as plt

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import custom functions for optimization
from src.solving import fischer_determinant
from src.data_structures import FischerModel
from src.optimization import find_optimal


# System of equation for pool-model and sensitivities
###############################
### USER DEFINES ODE SYSTEM ###
###############################
def pool_model_sensitivity(y, t, Q, P, Const):
    (a, b, c) = P
    (Temp,) = Q
    (n0, n_max) = Const
    (n, sa, sb, sc) = y
    return [
        (a*Temp + c) * (n -        n0 * np.exp(-b*Temp*t))*(1-n/n_max),
        (  Temp    ) * (n -        n0 * np.exp(-b*Temp*t))*(1-n/n_max) + (a*Temp + c) * (1 - 2*n/n_max + n0/n_max * np.exp(-b*Temp*t)) * sa,
        (a*Temp + c) * (    n0*t*Temp * np.exp(-b*Temp*t))*(1-n/n_max) + (a*Temp + c) * (1 - 2*n/n_max + n0/n_max * np.exp(-b*Temp*t)) * sb,
        (     1    ) * (n -        n0 * np.exp(-b*Temp*t))*(1-n/n_max) + (a*Temp + c) * (1 - 2*n/n_max + n0/n_max * np.exp(-b*Temp*t)) * sc
    ]


def jacobi(y, t, Q, P, Const):
    (n, sa, sb, sc) = y
    (a, b, c) = P
    (Temp,) = Q
    (n0, n_max) = Const
    dfdn = (a*Temp + c) * (1 - 2*n/n_max + n0/n_max * np.exp(-b*Temp*t))
    return np.array([
        [   dfdn,                                                                                             0,    0,    0   ],
        [(  Temp    ) * (1 - 2*n/n_max + n0/n_max * np.exp(-b*Temp*t)) + (a*Temp + c) * (1 - 2 / n_max) * sa, dfdn, 0,    0   ],
        [(a*Temp + c) * (  -  n0/n_max * t * Temp * np.exp(-b*Temp*t)) + (a*Temp + c) * (1 - 2 / n_max) * sb, 0,    dfdn, 0   ],
        [(     1    ) * (1 - 2*n/n_max + n0/n_max * np.exp(-b*Temp*t)) + (a*Temp + c) * (1 - 2 / n_max) * sc, 0,    0,    dfdn]
    ])


if __name__ == "__main__":
    ###############################
    ### USER DEFINES PARAMETERS ###
    ###############################

    # Define constants for the simulation duration
    n0 = 0.25
    n_max = 2e4
    Const = (n0, n_max)

    # Define initial parameter guesses
    a = 0.065
    b = 0.01
    c = 1.31

    P = (a, b, c)

    # Initial values for complete ODE (with S-Terms)
    t0 = 0.0
    y0 = np.array([n0, 0, 0, 0])

    # Define bounds for sampling
    temp_low = 2.0
    temp_high = 16.0
    n_temp = 20

    times_low = t0
    times_high = 15.0
    n_times = 20

    # Initial conditions with initial time
    y0_t0 = (y0, t0)

    # Construct parameter hyperspace
    n_times = 3
    n_temps = 2
    
    # Values for temperatures (Q-Values)
    q_values = [np.linspace(temp_low, temp_high, n_temps)]
    # Values for times (can be same for every temperature or different)
    # the distinction is made by dimension of array
    times = np.linspace(times_low, times_high, n_times)
    # times = np.array([np.linspace(times_low, times_high, n_times+2)[1:-1]] * n_temps)

    fsm = FischerModel(
        observable=fischer_determinant,
        times=times,
        parameters=P,
        q_values=q_values,
        constants=Const,
        y0_t0=(y0, t0),
        ode_func=pool_model_sensitivity,
        jacobian=jacobi
    )

    ###############################
    ### OPTIMIZATION FUNCTION ? ###
    ###############################
    bounds = [(times_low, times_high) for _ in range(len(times.flatten()))]
    d, S, C, fsm, solutions = find_optimal(times, bounds, fsm, "scipy_minimize")

    ###############################
    ##### PLOTTING FUNCTION ? #####
    ###############################
    fig, axs = plt.subplots(len(solutions), figsize=(12, 4*len(solutions)))
    for i, s in enumerate(solutions):
        t_values = np.linspace(t0, times_high)
        res = sp.integrate.odeint(pool_model_sensitivity, y0, t_values, args=(s[1], fsm.parameters, fsm.constants), Dfun=jacobi).T[0]
        axs[i].plot(t_values, res, color="blue", label="Exact solution")
        axs[i].plot(s[0], s[2][0], marker="o", color="k", linestyle="", label="Q_values: " + str(s[1]))
        axs[i].legend()
    fig.savefig("out/Result.svg")