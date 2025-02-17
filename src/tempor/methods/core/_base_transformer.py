import abc
from typing import Any

import pydantic

from tempor.core import pydantic_utils
from tempor.data import dataset
from tempor.log import logger

from . import _base_estimator as estimator


class BaseTransformer(estimator.BaseEstimator):
    def __init__(self, **params: Any) -> None:  # pylint: disable=useless-super-delegation
        super().__init__(**params)

    def transform(
        self,
        data: dataset.BaseDataset,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        logger.debug(f"Calling _transform() implementation on {self.__class__.__name__}")
        transformed_data = self._transform(data, *args, **kwargs)

        return transformed_data

    @pydantic_utils.validate_arguments(config=pydantic.ConfigDict(arbitrary_types_allowed=True))
    def fit_transform(
        self,
        data: dataset.BaseDataset,
        *args: Any,
        **kwargs: Any,
    ) -> dataset.BaseDataset:
        self.fit(data, *args, **kwargs)
        return self.transform(data, *args, **kwargs)

    @abc.abstractmethod
    def _transform(
        self, data: dataset.BaseDataset, *args: Any, **kwargs: Any
    ) -> dataset.BaseDataset:  # pragma: no cover
        ...
