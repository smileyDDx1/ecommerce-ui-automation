"""Loading test data from the JSON files in data/."""

import json
from functools import lru_cache

import pytest

from config.settings import DATA_DIR


@lru_cache
def load_json(name: str):
    """Return the parsed contents of data/<name>. Cached, so treat it as read-only."""
    with (DATA_DIR / name).open(encoding="utf-8") as fh:
        return json.load(fh)


def as_params(cases: list[dict], id_key: str = "id") -> list:
    """Turn a list of data cases into pytest params named after each case's id."""
    return [pytest.param(case, id=case[id_key]) for case in cases]
