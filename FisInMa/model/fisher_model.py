import numpy as np
# from dataclasses import dataclass
from copy import deepcopy
from pydantic.dataclasses import dataclass
from pydantic import root_validator, validator
try:
    from collections.abc import Callable
except:
    from typing import Callable
from typing import Optional, Union, Any, List, Tuple, Dict

from .preprocessing import VariableDefinition, MultiVariableDefinition, CovarianceDefinition


class Config:
    arbitrary_types_allowed = True
    smart_union = True
    validate_assignment = True


VARIABLE_DEF_TUPLE = Tuple[float, float, int, Optional[Any], Optional[Any], Optional[Any], Optional[Any]]
MULTIVARIABLE_DEF_TUPLE = Tuple[List[float], List[float], int, Optional[Any], Optional[Any], Optional[Any], Optional[Any]]


def list_to_list_of_vectors(ls: list) -> List[np.ndarray]:
    if all([type(l)==float for l in ls]):
        return [np.array(ls)]
    elif all([type(l)==list and all([type(li)==float for li in l]) for l in ls]):
        return [np.array(l) for l in ls]
    elif all([type(l)==np.ndarray and l.ndim==1 for l in ls]):
        return ls
    else:
        raise TypeError("Cannot convert list {} to list of numpy arrays".format(ls))


def list_to_nparray_of_float(ls: list) -> List[float]:
    if all([type(l)==float for l in ls]):
        return np.array(ls)
    elif all([type(l)==np.ndarray and l.size==1 for l in ls]):
        return np.array([float(l) for l in ls])
    else:
        raise TypeError("Cannot convert list {} to list of numpy arrays".format(ls))


def nparray_correct_shape_and_float(ls: np.ndarray) -> List[float]:
    acceptable_types = [float, int, np.int_, np.short, np.intc, np.longlong, np.half, np.float16, np.float32, np.single, np.double, np.longdouble, np.short]
    if all([type(l) in acceptable_types for l in ls]):
        return np.array([float(l) for l in ls])
    elif all([type(l)==np.ndarray and l.size==1 for l in ls]):
        return np.array([float(l) for l in ls])
    else:
        raise TypeError("Cannot convert list {} to list of numpy arrays".format(ls))


def nparray_to_list_of_vectors(npa: np.ndarray) -> List[np.ndarray]:
    if npa.ndim==1:
        return [npa]
    elif npa.ndim==0:
        return [np.array([npa], dtype=float)]
    else:
        raise ValueError("Dimension of the array must be <2")


def times_nparray_to_correct_shape(times: np.ndarray) -> np.ndarray:
    return times


TIMES_TYPE = Union[List, np.ndarray, VariableDefinition, None]
VECTORIZED_TYPE = Union[List, np.ndarray, MultiVariableDefinition, None]
SCALAR_TYPE = Union[List[float], np.ndarray, float, VariableDefinition, None]


_VECTORIZED_TYPE_CASTS = {
    list: list_to_list_of_vectors,
    np.ndarray: nparray_to_list_of_vectors,
    float: lambda x: [np.array([x])],
    dict: lambda x: MultiVariableDefinition(**x),
    tuple: lambda x: MultiVariableDefinition(*x),
    MultiVariableDefinition: lambda x: x,
}

_SCALAR_TYPE_CASTS = {
    float: lambda x: [x],
    list: list_to_nparray_of_float,
    np.ndarray: nparray_correct_shape_and_float,
    dict: lambda x: VariableDefinition(**x),
    tuple: lambda x: VariableDefinition(*x),
    VariableDefinition: lambda x: x,
}

_TIMES_TYPE_CASTS = {
    list: lambda x: np.array(x),
    np.ndarray: times_nparray_to_correct_shape,
    dict: lambda x: VariableDefinition(**x),
    tuple: lambda x: VariableDefinition(*x),
    VariableDefinition: lambda x: x,
}


def _general_validator(value, casts):
    if type(value) not in casts.keys():
        raise TypeError("We cannot process the type {}. Please specify one of the following types: {}".format(type(value), casts.keys()))
    else:
        return casts[type(value)](value)


@dataclass(config=Config)
class _FisherVariablesBase:
    ode_x0: VECTORIZED_TYPE
    ode_t0: SCALAR_TYPE
    times: Union[tuple, List[float], List[List[float]], np.ndarray, VariableDefinition, None]
    inputs: List#[SCALAR_TYPE]# list[Union[list[float],np.ndarray]]
    parameters: Tuple[float, ...]


@dataclass(config=Config)
class _FisherVariablesOptions:
    ode_args: Any = None
    identical_times: bool = False
    covariance: Union[float, Tuple[float, float], List[float], Tuple[str, float], Tuple[List[float], List[float]], Tuple[str, List[float]], CovarianceDefinition] = None


@dataclass(config=Config)
class _FisherOdeFunctions:
    ode_fun: Callable
    ode_dfdx: Callable
    ode_dfdp: Callable


@dataclass(config=Config)
class _FisherObservableFunctionsOptional:
    obs_fun: Optional[Callable] = None
    obs_dgdx: Optional[Callable] = None
    obs_dgdp: Optional[Callable] = None
    ode_dfdx0: Callable = None
    obs_dgdx0: Callable = None


@dataclass(config=Config)
class FisherVariables(_FisherVariablesOptions, _FisherVariablesBase):
    # TODO - Documentation Fisher Variables
    """Contains all necessary and optional numerical values needed to fully specify the model.
    Note that it is not possible to directly use this class to numerically solve the model
    since a initial guess for the corresponding values needs to be made.

    :param ode_x0: Initial values of the ODE.
    :type ode_x0: float, List[float], List[List[float]]
    :param ode_t0: Initial time point of the ODE.
    :type ode_t0: float, List[float]
    :param times: Time points at which the ODE should be evaluated.
    :type times:
    :param _FisherVariablesOptions:
    :type _FisherVariablesOptions: _type_
    """
    pass


@dataclass(config=Config)
class _FisherModelBase(_FisherOdeFunctions, _FisherVariablesBase):
    pass


@dataclass(config=Config)
class _FisherModelOptions(_FisherVariablesOptions, _FisherObservableFunctionsOptional):
    pass


@dataclass(config=Config)
class FisherModel(_FisherModelOptions, _FisherModelBase):
    # TODO - Documentation Fisher Model
    @validator('ode_x0', pre=True)
    def validate_ode_x0(cls, ode_x0):
        return _general_validator(ode_x0, _VECTORIZED_TYPE_CASTS)

    @validator('ode_t0', pre=True)
    def validate_ode_t0(cls, ode_t0):
        return _general_validator(ode_t0, _SCALAR_TYPE_CASTS)

    @validator('times', pre=True)
    def validate_times(cls, times):
        return _general_validator(times, _TIMES_TYPE_CASTS)

    @validator('inputs', pre=True, each_item=True)
    def validate_inputs(cls, inp):
        return _general_validator(inp, _SCALAR_TYPE_CASTS)

    @root_validator
    def all_observables_defined(cls, values):
        obs_names = ['obs_fun', 'obs_dgdx', 'obs_dgdp']
        c_obs = np.sum([n in values.keys() and callable(values[n]) for n in obs_names])
        if 1 < c_obs < 3:
            # TODO test this statement
            raise ValueError("Specify all of \'obs_fun\', \'obs_dgdx\' and \'obs_dgdp\' or none.")
        return values

    @root_validator
    def all_derivatives_x0_defined(cls, values):
        fun_names = ['ode_fun', 'ode_dfdx', 'ode_dfdp', 'ode_dfdx0']
        obs_names = ['obs_fun', 'obs_dgdx', 'obs_dgdp', 'obs_dgdx0']
        c_fun = np.sum([n in values.keys() and callable(values[n]) for n in fun_names])
        c_obs = np.sum([n in values.keys() and callable(values[n]) for n in obs_names])
        if c_obs > 0 and c_fun != c_obs:
            # TODO test this statement
            raise ValueError("Specify both \'ode_dfdx0\' and \'obs_dgdx0' when using observables.")
        return values


@dataclass(config=Config)
class _FisherModelParametrizedBase(_FisherOdeFunctions):
    variable_definitions: FisherVariables
    variable_values: FisherVariables

    # Define properties of class such that it can be used as a parametrized FisherModel
    # Get every possible numeric quantity that is stored in the model
    @property
    def ode_x0(self) -> np.ndarray:
        return self.variable_values.ode_x0

    @property
    def ode_t0(self) -> float:
        return self.variable_values.ode_t0

    @property
    def times(self) -> np.ndarray:
        return self.variable_values.times

    @property
    def inputs(self) -> list:
        return self.variable_values.inputs

    @property
    def parameters(self) -> tuple:
        return self.variable_values.parameters

    # TODO test this statement
    @property
    def ode_args(self) -> tuple:
        return self.variable_values.ode_args

    # These methods obtain only mutable quantities.
    # Return None or a list of None and values depending on which quantity is mutable
    # TODO test this statement
    @property
    def ode_x0_mut(self):
        if self.variable_definitions.ode_x0 is None:
            return None
        else:
            return self.variable_values.ode_x0

    # TODO test this statement
    @property
    def ode_t0_mut(self):
        if self.variable_definitions.ode_t0 is None:
            return None
        else:
            return self.variable_values.ode_t0

    # TODO test this statement
    @property
    def times_mut(self):
        if self.variable_definitions.times is None:
            return None
        else:
            return self.variable_values.times

    # TODO test this statement
    @property
    def inputs_mut(self):
        ret = []
        for q_val, q in zip(self.variable_values.inputs, self.variable_definitions.inputs):
            if q is None:
                ret.append(None)
            else:
                ret.append(q_val)
        return ret

    # These methods return the definition or None if the values were picked by hand
    @property
    def ode_x0_def(self):
        return self.variable_definitions.ode_x0

    @property
    def ode_t0_def(self):
        return self.variable_definitions.ode_t0

    @property
    def times_def(self):
        return self.variable_definitions.times

    @property
    def inputs_def(self):
        return self.variable_definitions.inputs

    # These methods modify mutable quantities
    @ode_x0.setter
    def ode_x0(self, x0) -> None:
        for i, y in enumerate(x0):
            self.variable_values.ode_x0[i] = y
            if self.variable_definitions.ode_x0 is None:
                raise AttributeError("Variable ode_x0 is not mutable!")

    @ode_t0.setter
    def ode_t0(self, t0) -> None:
        if type(t0) == float:
            # TODO test this statement
            self.variable_values.ode_t0 = np.array([t0])
        else:
            self.variable_values.ode_t0 = t0
        if self.variable_definitions.ode_t0 is None:
            raise AttributeError("Variable ode_t0 is not mutable!")

    @times.setter
    def times(self, times) -> None:
        self.variable_values.times = times
        if self.variable_definitions.times is None:
            raise AttributeError("Variable times is not mutable!")

    @inputs.setter
    def inputs(self, inputs) -> None:
        for i, q in enumerate(inputs):
            if q is not None:
                self.variable_values.inputs[i] = q
                if self.variable_definitions.inputs[i] is None:
                    raise AttributeError("Variable inputs at index {} is not mutable!".format(i))

    # TODO test this statement
    @ode_args.setter
    def ode_args(self, ode_args) -> None:
        self.variable_values.ode_args = ode_args


@dataclass(config=Config)
class _FisherModelParametrizedOptions(_FisherModelOptions):
    pass


@dataclass(config=Config)
class FisherModelParametrized(_FisherModelParametrizedOptions, _FisherModelParametrizedBase):
    # TODO - Documentation Fisher Model Parametrized
    def init_from(fsm: FisherModel):
        """Initialize a parametrized FisherModel with initial guesses for the sampled variables.

        :param fsm: A user-defined fisher model.
        :type fsm: FisherModel
        :raises TypeError: Currently does not accept sampling over initial values ode_x0.
        :return: Fully parametrized model with initial guesses which can be numerically solved.
        :rtype: FisherModelParametrized
        """
        # Create distinct classes to store
        # 1) Initial definition of model (ie. sample over certain variable; specify tuple of (min, max, n, dx, guess_method) or explicitly via np.array([...]))
        # 2) Explicit values together with initial guess such that every variable is parametrized
        variable_definitions = FisherVariables(
            fsm.ode_x0,
            fsm.ode_t0,
            fsm.times,
            fsm.inputs,
            fsm.parameters,
            fsm.ode_args,
            fsm.identical_times,
            fsm.covariance,
        )
        variable_values = deepcopy(variable_definitions)

        # Check which external inputs are being sampled
        _inputs_def = []
        _inputs_vals = []
        for q in fsm.inputs:
            q = _general_validator(q, _SCALAR_TYPE_CASTS)
            if type(q) == VariableDefinition:
                _inputs_def.append(q)
                _inputs_vals.append(q.initial_guess)
            else:
                _inputs_def.append(None)
                _inputs_vals.append(q)
        variable_definitions.inputs = _inputs_def
        variable_values.inputs = _inputs_vals
        inputs_shape = tuple(len(q) for q in _inputs_vals)

        # Check if we want to sample over initial values
        fsm.ode_x0 = _general_validator(fsm.ode_x0, _VECTORIZED_TYPE_CASTS)
        if type(fsm.ode_x0)==MultiVariableDefinition:
            variable_definitions.ode_x0 = fsm.ode_x0
            variable_values.ode_x0 = fsm.ode_x0.initial_guess
        else:
            variable_definitions.ode_x0 = None
            variable_values.ode_x0 = fsm.ode_x0

        # Check if time values are sampled
        fsm.times = _general_validator(fsm.times, _SCALAR_TYPE_CASTS)
        if type(fsm.times)==VariableDefinition:
            variable_definitions.times = fsm.times
            variable_values.times = fsm.times.initial_guess
        else:
            variable_definitions.times = None
            variable_values.times = fsm.times

        # Additionally if identical times were not defined, we need to extend the shape to the full one.
        if fsm.identical_times==False:
            variable_values.times = np.full(inputs_shape + variable_values.times.shape, variable_values.times)

        # Check if we want to sample over initial time
        fsm.ode_t0 = _general_validator(fsm.ode_t0, _SCALAR_TYPE_CASTS)
        if type(fsm.ode_t0)==VariableDefinition:
            variable_definitions.ode_t0 = fsm.ode_t0
            variable_values.ode_t0 = fsm.ode_t0.initial_guess
        else:
            variable_definitions.ode_t0 = None
            variable_values.ode_t0 = fsm.ode_t0

        # Check if we treat the initial values as a parameter
        if callable(fsm.ode_dfdx0):
            if callable(fsm.obs_fun) or callable(fsm.obs_dgdp) or callable(fsm.obs_dgdx):
                if not callable(fsm.obs_dgdx0):
                    # TODO test this statement
                    raise ValueError("ode_dfdx0 was specified and observable is probably used but obs_dgx0 was not given!")

            if len(variable_values.ode_x0) > 1:
                raise ValueError("Specify a single initial value to use it as a parameter. Sampling and treating x0 as parameter are complementary.")

        # Check if covariance was specified for our system
        n_x = len(variable_values.ode_x0[0])
        n_obs = n_x if callable(fsm.obs_fun)==False else np.array(fsm.obs_fun(variable_values.times[0], variable_values.ode_x0[0], [v[0] for v in variable_values.inputs], fsm.parameters, fsm.ode_args)).size

        if fsm.covariance is not None:
            if type(fsm.covariance) == tuple and len(fsm.covariance) == 2:
                c0 = fsm.covariance[0]
                c1 = fsm.covariance[1]

                if type(c0)==str and type(c1)==float:
                    if "rel" in c0:
                        covariance = CovarianceDefinition(relative=np.array(c1))
                    elif "abs" in c0:
                        covariance = CovarianceDefinition(absolute=np.array(c1))
                    else:
                        # TODO test this statement
                        raise ValueError("Cannot read input of covariance {}".format(fsm.covariance))
                if type(c0)==type(c1)==list:
                    if len(c0)!=n_x or len(c1)!=n_x:
                        # TODO test this statement
                        raise ValueError("Length of covariance list should be equal to number of observables")
                    covariance = CovarianceDefinition(absolute=np.array(c0), relative=np.array(c1))
                elif type(c0)==type(c1)==float:
                    # TODO test this statement FROM HERE
                    covariance = CovarianceDefinition(absolute=np.full((n_obs,), c0), relative=np.full((n_obs,), c1))
            elif type(fsm.covariance) == float:
                covariance = CovarianceDefinition(absolute=np.full((n_obs,), [fsm.covariance]))
            elif type(fsm.covariance) == list:
                if len(fsm.covariance)!=n_x:
                    raise ValueError("Length of covariance list should be equal to number of observables")
                covariance = CovarianceDefinition(absolute=np.array(fsm.covariance))
            elif type(fsm.covariance) == CovarianceDefinition:
                covariance = fsm.covariance
            else:
                raise ValueError("Cannot read input of covariance {}".format(fsm.covariance))
        else:
            covariance = CovarianceDefinition(absolute=None, relative=None)
        # TODO UNTIL HERE

        # Construct parametrized model class and return it
        fsmp = FisherModelParametrized(
            variable_definitions=variable_definitions,
            variable_values=variable_values,
            ode_fun=fsm.ode_fun,
            ode_dfdx=fsm.ode_dfdx,
            ode_dfdp=fsm.ode_dfdp,
            obs_fun=fsm.obs_fun,
            obs_dgdx=fsm.obs_dgdx,
            obs_dgdp=fsm.obs_dgdp,
            ode_dfdx0=fsm.ode_dfdx0,
            obs_dgdx0=fsm.obs_dgdx0,
            identical_times=fsm.identical_times,
            ode_args=fsm.ode_args,
            covariance=covariance,
        )
        return fsmp


@dataclass(config=Config)
class _FisherResultSingleBase(_FisherVariablesBase):
    ode_solution: Any#Union[list,np.ndarray]
    sensitivities: np.ndarray
    observables: np.ndarray


@dataclass(config=Config)
class _FisherResultSingleOptions(_FisherVariablesOptions):
    pass


@dataclass(config=Config)
class FisherResultSingle(_FisherResultSingleOptions, _FisherResultSingleBase):
    # TODO - Documentation Fisher Results Single
    pass


@dataclass(config=Config)
class _FisherResultsBase(_FisherModelParametrizedBase):
    criterion: float
    S: np.ndarray
    C: np.ndarray
    criterion_fun: Callable
    individual_results: list
    relative_sensitivities: bool
    

@dataclass(config=Config)
class _FisherResultsOptions(_FisherModelParametrizedOptions):
    penalty_discrete_summary: Any = None


@dataclass(config=Config)
class FisherResults(_FisherResultsOptions, _FisherResultsBase):
    # TODO - Documentation Fisher Results
    pass
