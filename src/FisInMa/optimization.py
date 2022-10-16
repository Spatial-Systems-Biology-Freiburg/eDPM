import numpy as np
import scipy as sp
import itertools

from FisInMa.data_structures import FischerModel, FischerModelParametrized
from FisInMa.solving import calculate_fischer_criterion, fischer_determinant


def discrete_penalizer(x, dx, x_offset=0.0):
    y = x - x_offset
    n, p = np.divmod(y, dx)
    _, q = np.divmod((n+1) * dx - y, dx)
    r = np.array([p, q]).min(axis=0)
    return 1 - 2 * r / dx


def __scipy_optimizer_function(X, fsmp: FischerModelParametrized, discrete=None, full=False):
    if fsmp.individual_times == True:
        times = np.sort(X.reshape(fsmp.times.shape), axis=-1)
    else:
        times = np.sort(X)
    
    fsmp.set_times(times)

    fsr = calculate_fischer_criterion(fsmp, False, fsmp.relative_sensitivities)

    if full:
        return fsr
    if discrete!=None:
        return -fsr.criterion * np.product(discrete_penalizer(fsmp.times.flatten(), discrete[0], discrete[1]))
    return - fsr.criterion


def __scipy_calculate_bounds_constraints(times0, fsmp: FischerModelParametrized, min_distance=None):
    x0 = times0.flatten()

    # Define linear constraints on times
    # Constraints are t0 <= t1 <= t2 ...
    # and tmin <= ti <= tmax
    n_times = fsmp.n_times
    n_q_values = np.product([len(q) for q in fsmp.q_values])
    A = np.zeros((n_times*2-1, n_times))
    for i in range(n_times-1):
        A[i][i] = 1.0
        A[i][i+1] = -1.0
    for i in range(n_times):
        A[i+n_times-1][i] = 1.0

    if fsmp.individual_times == False:
        B = A
        ub = np.append(np.full(n_times-1, 0.0 if min_distance==None else -min_distance), np.full((n_times,), fsmp.time_interval[1]))
        lb = np.append(np.full(n_times-1, - np.inf), np.full((n_times,), fsmp.time_interval[0]))
    else:
        B = np.zeros(((n_times*2 -1) * n_q_values, n_q_values * n_times))
        for i in range(n_q_values):
            tmp = np.concatenate([np.zeros((n_times*2-1, n_times)) for _ in range(i)] + [A] + [np.zeros((n_times*2-1, n_times)) for _ in range(n_q_values-1-i)], axis=1)
            B[i*(2*n_times-1):i*(2*n_times-1)+2*n_times-1] = tmp
    
        ub = np.concatenate([np.append(np.full(n_times-1, 0.0 if min_distance==None else -min_distance), np.full((n_times,), fsmp.time_interval[1]))] * n_q_values)
        lb = np.concatenate([np.append(np.full(n_times-1, - np.inf), np.full((n_times,), fsmp.time_interval[0]))] * n_q_values)

    constraints = sp.optimize.LinearConstraint(B, lb, ub)
    bounds = [(fsmp.time_interval[0], fsmp.time_interval[1]) for _ in range(len(x0))]

    return bounds, constraints


def __handle_custom_options(**args):
    custom_args = {}

    # Determine if times should have a minimum distance between each other
    if "min_distance" not in args.keys():
        min_distance=False
    else:
        min_distance=args.pop("min_distance")
    
    # Determine if results should be discretized
    if "discrete" not in args.keys():
        discrete=None
    else:
        discrete=args.pop("discrete")
        try:
            iter(discrete)
        except:
            discrete = (discrete, 0.0)
        if min_distance!=False:
            print("Warning: option 'discrete' overwrites option 'min_distance'")
        min_distance=discrete[0]
    
    custom_args["min_distance"] = min_distance
    custom_args["discrete"] = discrete
    return args, custom_args


def __scipy_differential_evolution(times0, fsmp: FischerModelParametrized, **args):
    # Filter custom options and scipy options
    args, custom_args = __handle_custom_options(**args)
    
    # Create constraints and bounds
    bounds, constraints = __scipy_calculate_bounds_constraints(times0, fsmp, custom_args["min_distance"])

    opt_args = {
        "func": __scipy_optimizer_function,
        "bounds": bounds,
        "constraints":constraints,
        "args":(fsmp, custom_args["discrete"]),
        "polish":False,
        "workers":-1,
        "updating":'deferred',
        "x0": times0.flatten()
    }
    opt_args.update(args)
    res = sp.optimize.differential_evolution(**opt_args)

    return __scipy_optimizer_function(res.x, fsmp, full=True)


def __scipy_brute(times0, fsmp: FischerModelParametrized, **args):
    # Filter custom options and scipy options
    args, custom_args = __handle_custom_options(**args)

    # Create constraints and bounds
    bounds, constraints = __scipy_calculate_bounds_constraints(times0, fsmp, custom_args["min_distance"])

    opt_args = {
        "func": __scipy_optimizer_function,
        "ranges": bounds,
        "args":(fsmp, custom_args["discrete"]),
        "finish":False,
        "workers":-1,
        "Ns":5
    }
    opt_args.update(args)
    res = sp.optimize.brute(**opt_args)

    return __scipy_optimizer_function(res, fsmp, full=True)


def __scipy_basinhopping(times0, fsmp: FischerModelParametrized, **args):
    # Filter custom options and scipy options
    args, custom_args = __handle_custom_options(**args)

    # Create constraints and bounds
    bounds, constraints = __scipy_calculate_bounds_constraints(times0, fsmp, custom_args["min_distance"])

    opt_args = {
        "func": __scipy_optimizer_function,
        "x0": times0.flatten(),
        "minimizer_kwargs":{"args":(fsmp, custom_args["discrete"]), "constraints": constraints, "bounds": bounds}
    }
    opt_args.update(args)
    res = sp.optimize.basinhopping(**opt_args)

    return __scipy_optimizer_function(res.x, fsmp, full=True)


def find_optimal(fsm: FischerModel, optimization_strategy: str, times_initial_guess=None, **args):
    fsmp, times_initial_guess = FischerModelParametrized.initialize_from(fsm, times_initial_guess)

    optimization_strategies = {
        "scipy_differential_evolution": __scipy_differential_evolution,
        "scipy_brute": __scipy_brute,
        "scipy_basinhopping": __scipy_basinhopping
    }
    if optimization_strategy not in optimization_strategies.keys():
        raise KeyError("Please specify one of the following optimization_strategies for optimization: " + str(optimization_strategies.keys()))

    return optimization_strategies[optimization_strategy](times_initial_guess, fsmp, **args)