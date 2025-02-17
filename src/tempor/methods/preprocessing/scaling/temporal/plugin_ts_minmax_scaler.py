import dataclasses
from typing import Any, Dict, List, Tuple

import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from typing_extensions import Self

from tempor.core import plugins
from tempor.data import dataset
from tempor.data.samples import TimeSeriesSamples
from tempor.methods.core import Params
from tempor.methods.core._params import CategoricalParams
from tempor.methods.preprocessing.scaling._base import BaseScaler


@dataclasses.dataclass
class TimeSeriesMinMaxScalerParams:
    """Initialization parameters for :class:`TimeSeriesMinMaxScaler`."""

    feature_range: Tuple[int, int] = (0, 1)
    """Desired range of transformed data. See `sklearn.preprocessing.MinMaxScaler`."""
    clip: bool = False
    """Set to True to clip transformed values of held-out data to provided ``feature_range``.
    See `sklearn.preprocessing.MinMaxScaler`.
    """


@plugins.register_plugin(name="ts_minmax_scaler", category="preprocessing.scaling.temporal")
class TimeSeriesMinMaxScaler(BaseScaler):
    ParamsDefinition = TimeSeriesMinMaxScalerParams
    params: TimeSeriesMinMaxScalerParams  # type: ignore

    def __init__(self, **params: Any) -> None:
        """MinMax scaling for the time-series data.

        Transform the temporal features by scaling each feature to a given range. This estimator scales and translates
        each feature individually such that it is in the given range on the training set, e.g. between zero and one.

        The time series data will be represented as a multi-index `(sample_idx, time_idx)` dataframe of features,
        and the scaling will be applied to this dataframe.

        Args:
            params:
                Parameters and defaults as defined in :class:`TimeSeriesMinMaxScalerParams`.

        Example:
            >>> from tempor import plugin_loader
            >>>
            >>> dataset = plugin_loader.get("prediction.one_off.sine", plugin_type="datasource").load()
            >>>
            >>> # Load the model:
            >>> model = plugin_loader.get("preprocessing.scaling.temporal.ts_minmax_scaler")
            >>>
            >>> # Train:
            >>> model.fit(dataset)
            TimeSeriesMinMaxScaler(...)
            >>>
            >>> # Scale:
            >>> scaled = model.transform(dataset)
        """
        super().__init__(**params)
        sklearn_params: Dict[str, Any] = dict(self.params)  # type: ignore
        sklearn_params["feature_range"] = tuple(sklearn_params["feature_range"])
        self.model = MinMaxScaler(**sklearn_params)

    def _fit(
        self,
        data: dataset.BaseDataset,
        *args: Any,
        **kwargs: Any,
    ) -> Self:
        self.model.fit(data.time_series.dataframe())
        return self

    def _transform(self, data: dataset.BaseDataset, *args: Any, **kwargs: Any) -> dataset.BaseDataset:
        temporal_data = data.time_series.dataframe()
        scaled = pd.DataFrame(self.model.transform(temporal_data))
        scaled.columns = temporal_data.columns
        scaled.index = temporal_data.index

        data.time_series = TimeSeriesSamples.from_dataframe(scaled)

        return data

    @staticmethod
    def hyperparameter_space(*args: Any, **kwargs: Any) -> List[Params]:
        return [
            CategoricalParams("clip", [True, False]),
        ]
