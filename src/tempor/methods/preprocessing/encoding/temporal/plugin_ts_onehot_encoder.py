import dataclasses
from typing import Any, Callable, Dict, List, Optional, Type, Union

import pandas as pd
import sklearn
from packaging.version import Version
from sklearn.preprocessing import OneHotEncoder
from typing_extensions import Literal, Self

from tempor.core import plugins
from tempor.data import dataset
from tempor.data.data_typing import FeatureIndex
from tempor.data.samples import TimeSeriesSamples
from tempor.methods.core import Params
from tempor.methods.core._params import CategoricalParams, FloatParams
from tempor.methods.preprocessing.encoding._base import BaseEncoder

# TODO: Factor out code for applying sklearn transformer to arbitrary subset of columns.


@dataclasses.dataclass
class TimeSeriesOneHotEncoderParams:
    """Initialization parameters for :class:`TimeSeriesOneHotEncoder`.

    See `sklearn.preprocessing.OneHotEncoder`.

    Note:
        ``sparse_output`` is always set to ``False``.
    """

    features: Optional[FeatureIndex] = None
    """Features to encode. If ``None``, all features will be encoded."""
    categories: Union[Literal["auto"], List] = "auto"
    """See ``categories`` in `sklearn.preprocessing.OneHotEncoder`"""
    drop: Union[None, Literal["first", "if_binary"], List] = None
    """See ``drop`` in `sklearn.preprocessing.OneHotEncoder`"""
    dtype: Type = float
    """See ``dtype`` in `sklearn.preprocessing.OneHotEncoder`"""
    handle_unknown: Literal["error", "ignore", "infrequent_if_exist"] = "error"
    """See ``handle_unknown`` in `sklearn.preprocessing.OneHotEncoder`"""
    min_frequency: Union[int, float, None] = None
    """See ``min_frequency`` in `sklearn.preprocessing.OneHotEncoder`"""
    max_categories: Union[int, None] = None
    """See ``max_categories`` in `sklearn.preprocessing.OneHotEncoder`"""
    feature_name_combiner: Union[Literal["concat"], Callable] = "concat"
    """See ``feature_name_combiner`` in `sklearn.preprocessing.OneHotEncoder`"""


@plugins.register_plugin(name="ts_onehot_encoder", category="preprocessing.encoding.temporal")
class TimeSeriesOneHotEncoder(BaseEncoder):
    ParamsDefinition = TimeSeriesOneHotEncoderParams
    params: TimeSeriesOneHotEncoderParams  # type: ignore

    def __init__(self, **params: Any) -> None:
        """One-hot encoding for the time series data.

        See `sklearn.preprocessing.OneHotEncoder` for details.

        Specify ``features`` list to encode only a subset of the features.

        Args:
            params:
                Parameters and defaults as defined in :class:`TimeSeriesOneHotEncoderParams`.

        Example:
            >>> from tempor import plugin_loader
            >>>
            >>> dataset = plugin_loader.get("prediction.temporal.dummy_prediction", plugin_type="datasource").load()
            >>>
            >>> # Get time series data with some categorical features.
            >>> import numpy as np
            >>> import pandas as pd
            >>> from tempor.data.samples import TimeSeriesSamples
            >>> ts_df = dataset.time_series.dataframe()
            >>> np.random.seed(777)
            >>> ts_df["categorical_feat_1"] = pd.Categorical(
            ...     np.random.choice(["a", "b", "c"], size=(len(ts_df),))
            ... )
            >>> ts_df["categorical_feat_2"] = pd.Categorical(np.random.choice(["D", "E"], size=(len(ts_df),)))
            >>> dataset.ts_df = TimeSeriesSamples.from_dataframe(ts_df)
            >>>
            >>> # Load the encoder:
            >>> enc = plugin_loader.get(
            ...     "preprocessing.encoding.temporal.ts_onehot_encoder",
            ...     features=["categorical_feat_1", "categorical_feat_2"],
            ... )
            >>>
            >>> # Fit:
            >>> enc.fit(dataset)
            TimeSeriesOneHotEncoder(...)
            >>>
            >>> # Encode:
            >>> encoded = enc.transform(dataset)
        """
        super().__init__(**params)
        self.features = self.params.features
        sklearn_params: Dict[str, Any] = {k: v for k, v in dict(self.params).items() if k != "features"}  # type: ignore
        sklearn_params["sparse_output"] = False

        if Version(sklearn.__version__) < Version("1.3"):  # pragma: no cover
            del sklearn_params["feature_name_combiner"]
        if Version(sklearn.__version__) < Version("1.1"):  # pragma: no cover
            del sklearn_params["min_frequency"]
            del sklearn_params["max_categories"]
        if Version(sklearn.__version__) < Version("1.2"):  # pragma: no cover
            sklearn_params["sparse"] = sklearn_params["sparse_output"]
            del sklearn_params["sparse_output"]

        self.model = OneHotEncoder(**sklearn_params)

    def _fit(
        self,
        data: dataset.BaseDataset,
        *args: Any,
        **kwargs: Any,
    ) -> Self:
        df_to_use = data.time_series.dataframe()
        if self.features is None:
            self.features = df_to_use.columns.tolist()
        df_to_use = df_to_use[self.features]

        self.model.fit(df_to_use)
        return self

    def _transform(self, data: dataset.BaseDataset, *args: Any, **kwargs: Any) -> dataset.BaseDataset:
        df_to_encode = data.time_series.dataframe()[self.features]
        encoded_arr = self.model.transform(df_to_encode)  # pyright: ignore
        encoded_col_names = self.model.get_feature_names_out()

        # Drop old columns.
        original_df = data.time_series.dataframe().drop(columns=self.features)

        # Append new encoded columns.
        encoded_df = pd.DataFrame(encoded_arr, columns=encoded_col_names, index=original_df.index)
        final_df = pd.concat([original_df, encoded_df], axis=1)

        data.time_series = TimeSeriesSamples.from_dataframe(final_df)

        return data

    @staticmethod
    def hyperparameter_space(*args: Any, **kwargs: Any) -> List[Params]:
        return [
            CategoricalParams("drop", ["first", "if_binary"]),
            CategoricalParams("handle_unknown", ["error", "ignore", "infrequent_if_exist"]),
            FloatParams("min_frequency", 0.0, 0.5),
        ]
