import dataclasses
from typing import TYPE_CHECKING, Any, List, Optional

import numpy as np
from typing_extensions import Self, get_args

from tempor.core import plugins
from tempor.data import dataset, samples
from tempor.methods.core import Params
from tempor.methods.core._params import CategoricalParams, FloatParams, IntegerParams
from tempor.methods.prediction.one_off.classification import BaseOneOffClassifier
from tempor.models import utils as model_utils
from tempor.models.constants import Nonlin, Samp
from tempor.models.ts_model import TimeSeriesModel, TSModelMode


@dataclasses.dataclass
class NeuralNetClassifierParams:
    """Initialization parameters for :class:`NeuralNetClassifier`."""

    n_static_units_hidden: int = 100
    """Number of hidden units for the static features."""
    n_static_layers_hidden: int = 2
    """Number of hidden layers for the static features."""
    n_temporal_units_hidden: int = 102
    """Number of hidden units for the temporal features."""
    n_temporal_layers_hidden: int = 2
    """Number of hidden layers for the temporal features."""
    n_iter: int = 500
    """Number of epochs."""
    mode: TSModelMode = "RNN"
    """Core neural net architecture. Available options: :obj:`~tempor.models.ts_model.TSModelMode`."""
    n_iter_print: int = 10
    """Number of epochs to print the loss."""
    batch_size: int = 100
    """Batch size."""
    lr: float = 1e-3
    """Learning rate."""
    weight_decay: float = 1e-3
    """l2 (ridge) penalty for the weights."""
    window_size: int = 1
    """How many hidden states to use for the outcome."""
    device: Optional[str] = None
    """String representing PyTorch device. If `None`, `~tempor.models.constants.DEVICE`."""
    dataloader_sampler: Optional[Samp] = None
    """Custom data sampler for training."""
    dropout: float = 0
    """Dropout value."""
    nonlin: Nonlin = "relu"
    """Activation for hidden layers. Available options: :obj:`~tempor.models.constants.Nonlin`."""
    random_state: int = 0
    """Random seed."""
    clipping_value: int = 1
    """Gradients clipping value. Zero disables the feature."""
    patience: int = 20
    """How many ``epoch * n_iter_print`` to wait without loss improvement."""
    train_ratio: float = 0.8
    """Train/test split ratio."""


@plugins.register_plugin(name="nn_classifier", category="prediction.one_off.classification")
class NeuralNetClassifier(BaseOneOffClassifier):
    ParamsDefinition = NeuralNetClassifierParams
    params: NeuralNetClassifierParams  # type: ignore

    def __init__(self, **params: Any) -> None:
        """Neural-net classifier.

        Args:
            params:
                Parameters and defaults as defined in :class:`NeuralNetClassifierParams`.

        Example:
            >>> from tempor import plugin_loader
            >>>
            >>> dataset = plugin_loader.get("prediction.one_off.sine", plugin_type="datasource").load()
            >>>
            >>> # Load the model:
            >>> model = plugin_loader.get("prediction.one_off.classification.nn_classifier", n_iter=50)
            >>>
            >>> # Train:
            >>> model.fit(dataset)
            NeuralNetClassifier(...)
            >>>
            >>> # Predict:
            >>> assert model.predict(dataset).numpy().shape == (len(dataset), 1)
        """
        super().__init__(**params)

        self.device = model_utils.get_device(self.params.device)
        self.dataloader_sampler = model_utils.get_sampler(self.params.dataloader_sampler)

        self.model: Optional[TimeSeriesModel] = None

    def _fit(
        self,
        data: dataset.BaseDataset,
        *args: Any,
        **kwargs: Any,
    ) -> Self:
        static, temporal, observation_times, outcome = self._unpack_dataset(data)
        outcome = outcome.squeeze()

        n_classes = len(np.unique(outcome))

        self.model = TimeSeriesModel(
            task_type="classification",
            n_static_units_in=static.shape[-1],
            n_temporal_units_in=temporal.shape[-1],
            n_temporal_window=temporal.shape[1],
            output_shape=[n_classes],
            n_static_units_hidden=self.params.n_static_units_hidden,
            n_static_layers_hidden=self.params.n_static_layers_hidden,
            n_temporal_units_hidden=self.params.n_temporal_units_hidden,
            n_temporal_layers_hidden=self.params.n_temporal_layers_hidden,
            n_iter=self.params.n_iter,
            mode=self.params.mode,
            n_iter_print=self.params.n_iter_print,
            batch_size=self.params.batch_size,
            lr=self.params.lr,
            weight_decay=self.params.weight_decay,
            window_size=self.params.window_size,
            device=self.device,
            dataloader_sampler=self.dataloader_sampler,
            dropout=self.params.dropout,
            nonlin=self.params.nonlin,
            random_state=self.params.random_state,
            clipping_value=self.params.clipping_value,
            patience=self.params.patience,
            train_ratio=self.params.train_ratio,
        )

        if TYPE_CHECKING:  # pragma: no cover
            assert isinstance(self.model, TimeSeriesModel)  # nosec B101

        self.model.fit(static, temporal, observation_times, outcome)
        return self

    def _predict(
        self,
        data: dataset.PredictiveDataset,
        *args: Any,
        **kwargs: Any,
    ) -> samples.StaticSamples:
        if self.model is None:
            raise RuntimeError("Fit the model first")
        static, temporal, observation_times, _ = self._unpack_dataset(data)

        preds = self.model.predict(static, temporal, observation_times)
        preds = preds.astype(float)

        preds = preds.reshape(-1, 1)
        return samples.StaticSamples.from_numpy(preds)

    def _predict_proba(
        self,
        data: dataset.PredictiveDataset,
        *args: Any,
        **kwargs: Any,
    ) -> samples.StaticSamples:
        if self.model is None:
            raise RuntimeError("Fit the model first")
        static, temporal, observation_times, _ = self._unpack_dataset(data)

        preds = self.model.predict_proba(static, temporal, observation_times)
        preds = preds.astype(float)

        return samples.StaticSamples.from_numpy(preds)

    @staticmethod
    def hyperparameter_space(*args: Any, **kwargs: Any) -> List[Params]:
        return [
            IntegerParams(name="n_static_units_hidden", low=100, high=1000),
            IntegerParams(name="n_static_layers_hidden", low=1, high=5),
            IntegerParams(name="n_temporal_units_hidden", low=100, high=1000),
            IntegerParams(name="n_temporal_layers_hidden", low=1, high=5),
            CategoricalParams(name="mode", choices=list(get_args(TSModelMode))),
            CategoricalParams(name="batch_size", choices=[64, 128, 256, 512]),
            CategoricalParams(name="lr", choices=[1e-3, 1e-4, 2e-4]),
            FloatParams(name="dropout", low=0, high=0.2),
            CategoricalParams(name="nonlin", choices=["relu", "elu", "leaky_relu", "selu"]),
        ]
