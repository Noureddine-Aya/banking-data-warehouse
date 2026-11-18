import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src")
)

from load_safe import load_districts


def test_dry_run_does_not_update():
    df = pd.DataFrame({
        "district_id": [69],
        "unemployment_95": [2.825]
    })

    mock_connection = MagicMock()
    mock_connection.execute.return_value.first.return_value = (None,)

    mock_engine = MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_connection

    with patch("load_safe.write_engine", mock_engine):
        load_districts(df, dry_run=True)

    assert mock_connection.execute.call_count == 1


def test_apply_updates_missing_value():
    df = pd.DataFrame({
        "district_id": [69],
        "unemployment_95": [2.825]
    })

    mock_connection = MagicMock()
    mock_connection.execute.return_value.first.return_value = (None,)

    mock_engine = MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_connection

    with patch("load_safe.write_engine", mock_engine):
        load_districts(df, dry_run=False)

    assert mock_connection.execute.call_count == 2



def test_duplicate_district_rejected():
    df = pd.DataFrame({
        "district_id": [1, 1],
        "unemployment_95": [2.0, 3.0]
    })

    with pytest.raises(ValueError):
        load_districts(df, dry_run=True)
