
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src")
)

from transform import transform_districts


def test_missing_values():
    df = pd.DataFrame({
        "district_id": [1, 2, 3],
        "unemployment_95": [2.0, None, 4.0],
        "crimes_95": [100.0, None, 300.0],
    })

    result = transform_districts(df)

    assert len(result) == 3
    assert result["unemployment_95"].iloc[1] == 3.0
    assert result["crimes_95"].iloc[1] == 200.0
    assert result.isna().sum().sum() == 0


def test_duplicate_districts():
    df = pd.DataFrame({
        "district_id": [1, 1],
        "unemployment_95": [2.0, 3.0],
        "crimes_95": [100.0, 200.0],
    })

    with pytest.raises(ValueError):
        transform_districts(df)


def test_source_not_modified():
    df = pd.DataFrame({
        "district_id": [1, 2, 3],
        "unemployment_95": [2.0, None, 4.0],
        "crimes_95": [100.0, None, 300.0],
    })

    original = df.copy(deep=True)

    transform_districts(df)

    pd.testing.assert_frame_equal(df, original)
