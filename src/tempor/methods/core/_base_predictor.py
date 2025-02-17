import abc
from typing import Any

import pydantic

from tempor.core import pydantic_utils
from tempor.data import dataset
from tempor.log import logger

from . import _base_estimator as estimator


class BasePredictor(estimator.BaseEstimator):
    def __init__(self, **params: Any) -> None:  # pylint: disable=useless-super-delegation
        super().__init__(**params)

    def predict(
        self,
        data: dataset.PredictiveDataset,
        *args: Any,
        **kwargs: Any,
    ) -> Any:  # TODO: Narrow down output formats later.
        if not self.is_fitted:
            raise ValueError("The model was not fitted, call `fit` first")
        if not data.predict_ready:
            raise ValueError(
                f"The dataset was not predict-ready, check that all necessary data components are present:\n{data}"
            )

        logger.debug(f"Calling _predict() implementation on {self.__class__.__name__}")
        prediction = self._predict(data, *args, **kwargs)

        return prediction

    def predict_proba(
        self,
        data: dataset.PredictiveDataset,
        *args: Any,
        **kwargs: Any,
    ) -> Any:  # TODO: Narrow down output formats later.
        if not self.is_fitted:
            raise ValueError("The model was not fitted, call `fit` first")
        if not data.predict_ready:
            raise ValueError(
                f"The dataset was not predict-ready, check that all necessary data components are present:\n{data}"
            )

        logger.debug(f"Calling _predict_proba() implementation on {self.__class__.__name__}")
        prediction = self._predict_proba(data, *args, **kwargs)

        return prediction

    def predict_counterfactuals(
        self,
        data: dataset.PredictiveDataset,
        *args: Any,
        **kwargs: Any,
    ) -> Any:  # TODO: Narrow down output formats later.
        if not self.is_fitted:
            raise ValueError("The model was not fitted, call `fit` first")
        if not data.predict_ready:
            raise ValueError(
                f"The dataset was not predict-ready, check that all necessary data components are present:\n{data}"
            )

        logger.debug(f"Calling _predict_counterfactuals() implementation on {self.__class__.__name__}")
        prediction = self._predict_counterfactuals(data, *args, **kwargs)

        return prediction

    # TODO: Add similar methods for predict_{proba,counterfactuals}.
    @pydantic_utils.validate_arguments(config=pydantic.ConfigDict(arbitrary_types_allowed=True))
    def fit_predict(
        self,
        data: dataset.PredictiveDataset,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        self.fit(data, *args, **kwargs)
        return self.predict(data, *args, **kwargs)

    @abc.abstractmethod
    def _predict(self, data: dataset.PredictiveDataset, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
        ...

    def _predict_proba(self, data: dataset.PredictiveDataset, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("`predict_proba` is supported only for classification tasks")

    def _predict_counterfactuals(self, data: dataset.PredictiveDataset, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("`predict_counterfactuals` is supported only for treatments tasks")
