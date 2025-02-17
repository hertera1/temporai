from pathlib import Path
from typing import Any, Union

import cloudpickle


def save(model: Any) -> bytes:
    return cloudpickle.dumps(model)


def load(buff: bytes) -> Any:
    return cloudpickle.loads(buff)


def save_to_file(path: Union[str, Path], model: Any) -> Any:
    path = Path(path)
    ppath = path.absolute().parent

    if not ppath.exists():
        ppath.mkdir(parents=True, exist_ok=True)

    with open(path, "wb") as f:
        return cloudpickle.dump(model, f)


def load_from_file(path: Union[str, Path]) -> Any:
    with open(path, "rb") as f:
        return cloudpickle.load(f)
