"""Mapping functions for WellsWatch prediction data."""

from __future__ import annotations

import zipfile
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import requests

from .zenodo import load_prediction_from_zenodo


NATURAL_EARTH_URL = (
    "https://naturalearth.s3.amazonaws.com/"
    "10m_cultural/ne_10m_admin_0_countries.zip"
)

CLASS_COLUMN = "realtime_pred_class_name"

CLASS_STYLES = {
    "non_red": {
        "color": "royalblue",
        "label": "Non-red wells",
    },
    "red": {
        "color": "red",
        "label": "Red wells",
    },
}


@lru_cache(maxsize=1)
def load_greece_boundary() -> gpd.GeoDataFrame:
    """Download and return the national boundary of Greece."""

    try:
        response = requests.get(
            NATURAL_EARTH_URL,
            timeout=120,
            headers={
                "User-Agent": "wellswatch/0.1.0",
            },
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ConnectionError(
            "Could not download the Greece boundary."
        ) from exc

    try:
        archive = zipfile.ZipFile(
            BytesIO(response.content)
        )
    except zipfile.BadZipFile as exc:
        raise ValueError(
            "The downloaded Natural Earth file is not a valid ZIP archive."
        ) from exc

    with TemporaryDirectory() as temporary_directory:
        archive.extractall(temporary_directory)

        shapefiles = list(
            Path(temporary_directory).glob("*.shp")
        )

        if not shapefiles:
            raise FileNotFoundError(
                "No shapefile was found in the Natural Earth archive."
            )

        world = gpd.read_file(shapefiles[0])

    mask = pd.Series(
        False,
        index=world.index,
    )

    possible_name_columns = [
        "ADMIN",
        "NAME_EN",
        "NAME",
        "SOVEREIGNT",
    ]

    for column in possible_name_columns:
        if column in world.columns:
            mask = mask | (
                world[column]
                .astype(str)
                .str.strip()
                .str.casefold()
                .eq("greece")
            )

    greece = world.loc[mask].copy()

    if greece.empty:
        raise ValueError(
            "Greece was not found in the Natural Earth dataset."
        )

    return greece.to_crs("EPSG:4326")


def predictions_to_geodataframe(
    data: pd.DataFrame,
) -> gpd.GeoDataFrame:
    """Convert prediction data to a GeoDataFrame."""

    required_columns = [
        "lon",
        "lat",
        CLASS_COLUMN,
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing columns required for mapping: "
            + ", ".join(missing_columns)
        )

    result = data.copy()

    result["lon"] = pd.to_numeric(
        result["lon"],
        errors="coerce",
    )

    result["lat"] = pd.to_numeric(
        result["lat"],
        errors="coerce",
    )

    if result[["lon", "lat"]].isna().any().any():
        raise ValueError(
            "Invalid or missing longitude/latitude values were found."
        )

    result[CLASS_COLUMN] = (
        result[CLASS_COLUMN]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    return gpd.GeoDataFrame(
        result,
        geometry=gpd.points_from_xy(
            result["lon"],
            result["lat"],
        ),
        crs="EPSG:4326",
    )


def plot_wells(
    data: pd.DataFrame,
    save_path: str | Path | None = None,
    marker_size: float = 14,
    show: bool = True,
):
    """
    Plot red and non-red wells on a map of Greece.

    Parameters
    ----------
    data:
        WellsWatch prediction data.
    save_path:
        Optional path for saving the map.
    marker_size:
        Size of well markers.
    show:
        Whether to display the map.

    Returns
    -------
    tuple
        Matplotlib figure and axes.
    """

    wells = predictions_to_geodataframe(data)
    greece = load_greece_boundary().copy()

    figure, axis = plt.subplots(
        figsize=(9, 10),
    )

    greece.plot(
        ax=axis,
        color="whitesmoke",
        edgecolor="black",
        linewidth=0.8,
    )

    for class_name in ["non_red", "red"]:
        subset = wells[
            wells[CLASS_COLUMN] == class_name
        ]

        if subset.empty:
            continue

        style = CLASS_STYLES[class_name]

        subset.plot(
            ax=axis,
            color=style["color"],
            markersize=marker_size,
            alpha=0.80,
            label=style["label"],
            edgecolor="white",
            linewidth=0.15,
        )

    if "prediction_date" in wells.columns:
        prediction_dates = (
            pd.to_datetime(
                wells["prediction_date"],
                errors="coerce",
            )
            .dropna()
            .unique()
        )

        if len(prediction_dates) == 1:
            prediction_date = pd.Timestamp(
                prediction_dates[0]
            )

            title = (
                "Predicted groundwater status in Greece\n"
                f"{prediction_date:%d %B %Y}"
            )
        else:
            title = "Predicted groundwater status in Greece"
    else:
        title = "Predicted groundwater status in Greece"

    minimum_x, minimum_y, maximum_x, maximum_y = (
        greece.total_bounds
    )

    axis.set_xlim(
        minimum_x - 0.35,
        maximum_x + 0.35,
    )

    axis.set_ylim(
        minimum_y - 0.25,
        maximum_y + 0.25,
    )

    axis.set_title(
        title,
        fontsize=14,
    )

    axis.set_xlabel("Longitude")
    axis.set_ylabel("Latitude")

    axis.grid(
        visible=True,
        linewidth=0.4,
        alpha=0.35,
    )

    axis.legend(
        title="Predicted status",
        loc="lower left",
    )

    figure.tight_layout()

    if save_path is not None:
        output_path = Path(save_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        figure.savefig(
            output_path,
            dpi=300,
            bbox_inches="tight",
        )

    if show:
        plt.show()

    return figure, axis


def show_map(
    year: int,
    month: int = 8,
    day: int = 1,
    save_path: str | Path | None = None,
    marker_size: float = 14,
    show: bool = True,
):
    """
    Download predictions from Zenodo and plot them.

    Returns the prediction data, figure and axes.
    """

    data = load_prediction_from_zenodo(
        year=year,
        month=month,
        day=day,
    )

    figure, axis = plot_wells(
        data=data,
        save_path=save_path,
        marker_size=marker_size,
        show=show,
    )

    return data, figure, axis