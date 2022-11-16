import matplotlib.pyplot as plt
import numpy as np
import scipy as sp
from pathlib import Path
import itertools

from FisInMa.model import FisherResults, FisherModelParametrized
from FisInMa.solving import calculate_fisher_criterion


def plot_template(fsr: FisherResults, sol, sol_new, y_design, y_model, outdir, additional_name, y_name, i, j, k=None, file_format="svg"):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(sol_new.times, y_model, color="#21918c", label="Model Solution", linewidth=2)

    # Plot sampled time points
    ax.scatter(sol.times, y_design, s=160, alpha=0.5, color="#440154", label="Optimal Design")
    ax.set_xlabel("Time", fontsize=15)
    ax.set_ylabel(y_name, fontsize=15)
    ax.tick_params(axis="y", labelsize=13)
    ax.tick_params(axis="x", labelsize=13)
    ax.legend(fontsize=15, framealpha=0.5)
    if k == None:
        save_name = "{}_Results_{}_{}_{}_{:03.0f}_x_{:02.0f}.{}".format(y_name, getattr(fsr.ode_fun, '__name__', 'unknown'), getattr(fsr.criterion_fun, '__name__', 'unknown'), additional_name, i, j, file_format)
        title_name = f"Observable {j}, \n Inputs {[round(inp, 1) for inp in sol.inputs]},\n Times {[round(t, 1) for t in sol.times]}"
    else:
        save_name = "{}_Results_{}_{}_{}_{:03.0f}_x_{:02.0f}_p_{:02.0f}.{}".format(y_name, getattr(fsr.ode_fun, '__name__', 'unknown'), getattr(fsr.criterion_fun, '__name__', 'unknown'), additional_name, i, j, k, file_format)
        title_name = f"Observable {j},  Parameter {k}, \n Inputs {[round(inp, 1) for inp in sol.inputs]},\n Times {[round(t, 1) for t in sol.times]}"
    ax.set_title(title_name, fontsize=15)

    fig.savefig(outdir / Path(save_name), bbox_inches='tight')

    # Remove figure to free space
    plt.close(fig)


def plot_all_odes(fsr: FisherResults, fsr_plot=None, outdir=Path("."), additional_name="", **kwargs):
    """Plots results of the ODE with time points at which the ODE is evaluated
    for every input combination.

    :param fsr: Results generated by an optimization or solving routine.
    :type fsr: FisherResults
    :param outdir: Output directory to store the images in. Defaults to Path(".").
    :type outdir: Path, optional
    """
    if fsr_plot == None:
        fsr_plot = get_frs_plot(fsr)

    for i, (sol, sol_new) in enumerate(zip(fsr.individual_results, fsr_plot.individual_results)):
        n_x = len(fsr.ode_x0[0])

        # Plot the solution and store in individual files
        for j in range(n_x):
            plot_template(fsr, sol, sol_new, sol.ode_solution.y[j], sol_new.ode_solution.y[j], outdir, additional_name, "ODE", i, j, **kwargs)


def plot_all_observables(fsr: FisherResults, fsr_plot=None, outdir=Path("."), additional_name="", **kwargs):
    """Plots the observables with time points chosen for Optimal Experimental Design.

    :param fsr: Results generated by an optimization or solving routine.
    :type fsr: FisherResults
    :param outdir: Output directory to store the images in. Defaults to Path(".").
    :type outdir: Path, optional
    """ 
    if fsr_plot == None:
        fsr_plot = get_frs_plot(fsr)

    for i, (sol, sol_new) in enumerate(zip(fsr.individual_results, fsr_plot.individual_results)):
        n_x = len(fsr.ode_x0[0])
        n_obs = len(fsr_plot.obs_fun(sol.ode_t0, sol.ode_x0, sol.inputs, sol.parameters, sol.ode_args)) if callable(fsr_plot.obs_fun) else n_x

        # Plot the solution and store in individual files
        for j in range(n_obs):
            plot_template(fsr, sol, sol_new, sol.observables[j], sol_new.observables[j], outdir, additional_name, "Observable", i, j, **kwargs)


def plot_all_sensitivities(fsr: FisherResults, fsr_plot=None, outdir=Path("."), additional_name="", **kwargs):
    r"""Plots results of the sensitivities :math:`s_{ij} = \frac{\partial y_i}{\partial p_j}` or , in case of relative sensitivities, :math:`s_{ij} = \frac{\partial y_i}{\partial p_j} \frac{p_j}{y_i}` with time points at which the ODE is evaluated
    for every input combination.
    :param fsr: Results generated by an optimization or solving routine.
    :type fsr: FisherResults
    :param outdir: Output directory to store the images in. Defaults to Path(".")., defaults to Path(".")
    :type outdir: Path, optional
    """
    if fsr_plot == None:
        fsr_plot = get_frs_plot(fsr)

    for i, (sol, sol_new) in enumerate(zip(fsr.individual_results, fsr_plot.individual_results)):
        n_x = len(fsr.ode_x0[0])
        n_obs = len(fsr_plot.obs_fun(sol.ode_t0, sol.ode_x0, sol.inputs, sol.parameters, sol.ode_args)) if callable(fsr_plot.obs_fun) else n_x
        n_p = len(fsr_plot.parameters)
        n_p_full = n_p + (n_x if callable(fsr.ode_dfdx0) else 0)

        for j, k in itertools.product(range(n_obs), range(n_p_full)):
            plot_template(fsr, sol, sol_new, sol.sensitivities[k, j], sol_new.sensitivities[k, j], outdir, additional_name, "Sensitivity", i, j, k, **kwargs)


def plot_all_solutions(fsr: FisherResults, fsr_plot=None,  outdir=Path("."), additional_name="", **kwargs):
    r"""Combines functionality of plot_all_odes and plot_all_sensitivities.
    Plots results of the ODE with time points at which the ODE is evaluated
    and results of the sensitivities :math:`s_{ij} = \frac{\partial y_i}{\partial p_j}`
    with time points at which the ODE is evaluated for every input combination.

    :param fsr: Results generated by an optimization or solving routine.
    :type fsr: FisherResults
    :param outdir: Output directory to store the images in. Defaults to Path(".")., defaults to Path(".")
    :type outdir: Path, optional
    """
    if fsr_plot == None:
        fsr_plot = get_frs_plot(fsr)

    plot_all_odes(fsr, fsr_plot, outdir, additional_name, **kwargs)
    plot_all_sensitivities(fsr, fsr_plot, outdir, additional_name, **kwargs)
    plot_all_observables(fsr, fsr_plot, outdir, additional_name, **kwargs)


def get_frs_plot(fsr: FisherResults):
    times_low = fsr.ode_t0[0]
    times_high = fsr.times_def.ub if fsr.times_def is not None else np.max(fsr.times)
    t_values = np.linspace(times_low, times_high, 1000)

    fsmp_args = {key:value for key, value in fsr.__dict__.items() if not key.startswith('_')}

    fsmp = FisherModelParametrized(**fsmp_args)
    fsmp.times = np.full(fsmp.times.shape[0:-1] + (t_values.size,), t_values)

    frs_plot = calculate_fisher_criterion(fsmp, fsr.criterion_fun, relative_sensitivities=fsr.relative_sensitivities, verbose=False)
    return frs_plot

# TODO - find way to plot json dump from database
