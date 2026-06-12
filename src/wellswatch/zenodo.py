"""Functions for reading WellsWatch prediction files."""

from __future__ import annotations

import re
from datetime import date
from io import BytesIO
from pathlib import Path

import pandas as pd
import requests


ZENODO_RECORD_ID = "20427364"
ZENODO_API_URL = "https://zenodo.org/api/records/{record_id}"

REQUIRED_COLUMNS = [
    "row_id",
    "station_code",
    "lon",
    "lat",
    "realtime_pred_class_name",
    "realtime_pred_red_probability",
]

VALID_CLASSES = {"red", "non_red"}


def extract_prediction_date(filename: str | Path) -> date:
    """Extract a prediction date from a WellsWatch filename."""

    name = Path(filename).name

    match = re.search(
        r"pred_(\d{4})_(\d{2})_(\d{2})",
        name,
    )

    if match is None:
        raise ValueError(
            f"Could not extract a prediction date from: {name}"
        )

    year, month, day = map(int, match.groups())

    return date(year, month, day)


def validate_predictions(data: pd.DataFrame) -> None:
    """Validate prediction columns and values."""

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing_columns)
        )

    essential_columns = [
        "station_code",
        "lon",
        "lat",
        "realtime_pred_class_name",
        "realtime_pred_red_probability",
    ]

    columns_with_missing_values = [
        column
        for column in essential_columns
        if data[column].isna().any()
    ]

    if columns_with_missing_values:
        raise ValueError(
            "Missing values found in: "
            + ", ".join(columns_with_missing_values)
        )

    observed_classes = set(
        data["realtime_pred_class_name"]
        .astype(str)
        .str.strip()
        .str.lower()
        .unique()
    )

    invalid_classes = observed_classes - VALID_CLASSES

    if invalid_classes:
        raise ValueError(
            "Unexpected prediction classes: "
            + ", ".join(sorted(invalid_classes))
        )

    if not data["lon"].between(-180, 180).all():
        raise ValueError(
            "Invalid longitude values were found."
        )

    if not data["lat"].between(-90, 90).all():
        raise ValueError(
            "Invalid latitude values were found."
        )

    if not data[
        "realtime_pred_red_probability"
    ].between(0, 1).all():
        raise ValueError(
            "Red probabilities must be between 0 and 1."
        )


def _prepare_predictions(
    data: pd.DataFrame,
    filename: str,
) -> pd.DataFrame:
    """Normalize, validate and add the prediction date."""

    result = data.copy()

    numeric_columns = [
        "lon",
        "lat",
        "realtime_pred_red_probability",
    ]

    for column in numeric_columns:
        if column in result.columns:
            result[column] = pd.to_numeric(
                result[column],
                errors="coerce",
            )

    if "realtime_pred_class_name" in result.columns:
        result["realtime_pred_class_name"] = (
            result["realtime_pred_class_name"]
            .astype(str)
            .str.strip()
            .str.lower()
        )

    validate_predictions(result)

    result["prediction_date"] = pd.Timestamp(
        extract_prediction_date(filename)
    )

    return result


def load_prediction_file(
    file_path: str | Path,
) -> pd.DataFrame:
    """Read a local WellsWatch Excel or CSV file."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Prediction file not found: {path}"
        )

    if path.suffix.lower() == ".xlsx":
        data = pd.read_excel(path)
    elif path.suffix.lower() == ".csv":
        data = pd.read_csv(path)
    else:
        raise ValueError(
            "Supported file types are .xlsx and .csv."
        )

    return _prepare_predictions(
        data=data,
        filename=path.name,
    )


def list_zenodo_files(
    record_id: str | int = ZENODO_RECORD_ID,
) -> list[str]:
    """Return the filenames available in a Zenodo record."""

    url = ZENODO_API_URL.format(
        record_id=record_id,
    )

    try:
        response = requests.get(
            url,
            timeout=60,
            headers={
                "User-Agent": "wellswatch/0.1.0",
            },
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ConnectionError(
            f"Could not access Zenodo record {record_id}."
        ) from exc

    metadata = response.json()

    return [
        item.get("key") or item.get("filename")
        for item in metadata.get("files", [])
        if item.get("key") or item.get("filename")
    ]


def load_prediction_from_zenodo(
    year: int,
    month: int = 8,
    day: int = 1,
    record_id: str | int = ZENODO_RECORD_ID,
) -> pd.DataFrame:
    """
    Download and read predictions directly from Zenodo.

    Example
    -------
    data = load_prediction_from_zenodo(2025, 8, 1)
    """

    url = ZENODO_API_URL.format(
        record_id=record_id,
    )

    try:
        response = requests.get(
            url,
            timeout=60,
            headers={
                "User-Agent": "wellswatch/0.1.0",
            },
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ConnectionError(
            f"Could not access Zenodo record {record_id}."
        ) from exc

    metadata = response.json()
    files = metadata.get("files", [])

    date_token = (
        f"pred_{year:04d}_{month:02d}_{day:02d}"
    ).lower()

    matches = []

    for item in files:
        filename = (
            item.get("key")
            or item.get("filename")
            or ""
        )

        if (
            date_token in filename.lower()
            and Path(filename).suffix.lower()
            in {".xlsx", ".csv"}
        ):
            matches.append(item)

    if not matches:
        available_files = [
            item.get("key") or item.get("filename")
            for item in files
        ]

        raise FileNotFoundError(
            f"No prediction file was found for "
            f"{year:04d}-{month:02d}-{day:02d}. "
            f"Available files: {available_files}"
        )

    if len(matches) > 1:
        matched_names = [
            item.get("key") or item.get("filename")
            for item in matches
        ]

        raise ValueError(
            "More than one matching file was found: "
            + ", ".join(matched_names)
        )

    selected_file = matches[0]

    filename = (
        selected_file.get("key")
        or selected_file.get("filename")
    )

    file_links = selected_file.get("links", {})

    download_url = (
        file_links.get("self")
        or file_links.get("content")
        or file_links.get("download")
    )

    if not download_url:
        raise ValueError(
            f"No download URL was found for {filename}. "
            f"Available link fields: {list(file_links)}"
        )

    try:
        file_response = requests.get(
            download_url,
            timeout=120,
            headers={
                "User-Agent": "wellswatch/0.1.0",
            },
        )
        file_response.raise_for_status()
    except requests.RequestException as exc:
        raise ConnectionError(
            f"Could not download {filename} from Zenodo."
        ) from exc

    content = BytesIO(
        file_response.content,
    )

    suffix = Path(filename).suffix.lower()

    if suffix == ".xlsx":
        data = pd.read_excel(content)
    elif suffix == ".csv":
        data = pd.read_csv(content)
    else:
        raise ValueError(
            f"Unsupported Zenodo file type: {suffix}"
        )

    result = _prepare_predictions(
        data=data,
        filename=filename,
    )

    result.attrs["source"] = "Zenodo"
    result.attrs["zenodo_record_id"] = str(
        record_id,
    )
    result.attrs["source_filename"] = filename

    return result

