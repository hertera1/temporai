import torch
from typing_extensions import Literal

DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

EPS: float = torch.finfo(torch.float32).eps

ModelTaskType = Literal["classification", "regression"]
ODEBackend = Literal["ode", "cde", "laplace"]

Nonlin = Literal[
    "none",
    "elu",
    "relu",
    "leaky_relu",
    "selu",
    "tanh",
    "sigmoid",
    "softmax",
    "gumbel_softmax",
]
"""Possible values specifying a nonlinearity."""

Samp = Literal[
    "BatchSampler",
    "RandomSampler",
    "Sampler",
    "SequentialSampler",
    "SubsetRandomSampler",
    "WeightedRandomSampler",
]
"""Possible values specifying a Sampler."""
