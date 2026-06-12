"""WellsWatch: groundwater-status visualization for Greece."""

from .mapping import (
    load_greece_boundary,
    plot_wells,
    predictions_to_geodataframe,
    show_map,
)
from .zenodo import (
    extract_prediction_date,
    list_zenodo_files,
    load_prediction_file,
    load_prediction_from_zenodo,
    validate_predictions,
)

__version__ = "0.1.0"

__all__ = [
    "extract_prediction_date",
    "list_zenodo_files",
    "load_greece_boundary",
    "load_prediction_file",
    "load_prediction_from_zenodo",
    "plot_wells",
    "predictions_to_geodataframe",
    "show_map",
    "validate_predictions",
]