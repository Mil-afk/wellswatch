from datetime import date

import pandas as pd
import pytest

from wellswatch import (
    extract_prediction_date,
    predictions_to_geodataframe,
    validate_predictions,
)


def sample_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "row_id": [1, 2],
            "station_code": ["A", "B"],
            "lon": [22.9, 23.7],
            "lat": [40.6, 38.0],
            "realtime_pred_class_name": [
                "red",
                "non_red",
            ],
            "realtime_pred_red_probability": [
                0.82,
                0.21,
            ],
        }
    )


def test_extract_prediction_date():
    result = extract_prediction_date(
        "13_pred_2025_08_01_with_predictions_01.xlsx"
    )

    assert result == date(2025, 8, 1)


def test_validate_predictions():
    validate_predictions(sample_data())


def test_missing_required_column():
    data = sample_data().drop(
        columns=["station_code"]
    )

    with pytest.raises(
        ValueError,
        match="Missing required columns",
    ):
        validate_predictions(data)


def test_invalid_prediction_class():
    data = sample_data()

    data.loc[0, "realtime_pred_class_name"] = (
        "unknown"
    )

    with pytest.raises(
        ValueError,
        match="Unexpected prediction classes",
    ):
        validate_predictions(data)


def test_predictions_to_geodataframe():
    geodata = predictions_to_geodataframe(
        sample_data()
    )

    assert geodata.crs.to_string() == "EPSG:4326"
    assert len(geodata) == 2
    assert geodata.geometry.notna().all()