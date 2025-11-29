"""
NEMT Trip Data Parser

A flexible, framework-agnostic Python module for parsing and standardizing
NEMT trip data from multiple clinic sources.

Quick Start:
    from nemt_parser import TripParser, MappingRepository

    # Initialize with database
    repo = MappingRepository("sqlite:///my_trips.db")
    parser = TripParser(mapping_repository=repo)

    # Parse Excel file
    result = parser.parse_excel("clinic_data.xlsx", clinic_id="clinic_a")

    # Access parsed trips
    for trip in result.trips:
        print(trip.patient_name, trip.appointment_date)
"""

__version__ = "0.1.0"

# Core exports
from .core.parser import TripParser
from .core.models import (
    Trip,
    TripType,
    ColumnMapping,
    ParseResult,
    MappingSuggestion,
)
from .core.mapper import ColumnMapper
from .core.validator import DataValidator

# Database exports
from .database.repositories import (
    MappingRepository,
    TripRepository,
    UploadHistoryRepository,
)

__all__ = [
    # Version
    "__version__",
    # Core
    "TripParser",
    "Trip",
    "TripType",
    "ColumnMapping",
    "ParseResult",
    "MappingSuggestion",
    "ColumnMapper",
    "DataValidator",
    # Database
    "MappingRepository",
    "TripRepository",
    "UploadHistoryRepository",
]
