"""
Shared fixtures for NEMT Trip Parser test suite.
"""

import sys
import os

# Add project root to path so tests can import root-level modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import tempfile
from datetime import date, time, datetime
from pathlib import Path

from nemt_parser.core.models import Trip, TripType, ColumnMapping, ParseResult
from nemt_parser.database.repositories import (
    MappingRepository,
    TripRepository,
    UploadHistoryRepository,
)


# ---------------------------------------------------------------------------
# Sample Trip objects
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_trip():
    """A fully-populated Trip object for testing."""
    return Trip(
        patient_name="Jane Doe",
        patient_phone="(305) 555-1234",
        medicaid_id="MCD987654321",
        date_of_birth=date(1960, 3, 15),
        pickup_address="100 NW 1st Ave",
        pickup_city="Miami",
        pickup_state="FL",
        pickup_zip="33101",
        dropoff_address="200 SW 2nd St",
        dropoff_city="Miami",
        dropoff_state="FL",
        dropoff_zip="33130",
        appointment_date=date(2025, 6, 15),
        appointment_time=time(10, 30),
        trip_type=TripType.ROUND_TRIP,
        wheelchair=False,
        stretcher=False,
        ambulatory=True,
        notes="Needs walker assistance",
        source_clinic_id="test_clinic",
        uploaded_at=datetime(2025, 6, 15, 8, 0, 0),
    )


@pytest.fixture
def wheelchair_trip(sample_trip):
    """Trip requiring wheelchair."""
    return sample_trip.model_copy(update={"wheelchair": True, "ambulatory": False})


@pytest.fixture
def stretcher_trip(sample_trip):
    """Trip requiring stretcher."""
    return sample_trip.model_copy(update={"stretcher": True, "ambulatory": False})


@pytest.fixture
def minimal_trip():
    """Trip with only required fields."""
    return Trip(
        patient_name="John Smith",
        medicaid_id="MCD111222333",
        pickup_address="1 Main St",
        pickup_city="Orlando",
        pickup_zip="32801",
        dropoff_address="2 Hospital Blvd",
        dropoff_city="Orlando",
        dropoff_zip="32806",
        appointment_date=date(2025, 7, 1),
    )


# ---------------------------------------------------------------------------
# Column mapping fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_mapping():
    """A standard column mapping for Clinic A style headers."""
    return ColumnMapping(
        clinic_id="test_clinic",
        clinic_name="Test Medical Center",
        patient_name="Patient Name",
        patient_phone="Phone",
        medicaid_id="Medicaid #",
        date_of_birth="DOB",
        pickup_address="Pick-up Address",
        pickup_city="Pick-up City",
        pickup_state="Pick-up State",
        pickup_zip="Pick-up ZIP",
        dropoff_address="Drop-off Address",
        dropoff_city="Drop-off City",
        dropoff_state="Drop-off State",
        dropoff_zip="Drop-off ZIP",
        appointment_date="Appt Date",
        appointment_time="Appt Time",
        trip_type="Trip Type",
        wheelchair="Wheelchair?",
        notes="Notes",
    )


@pytest.fixture
def sample_excel_columns():
    """Column names that match sample_mapping."""
    return [
        "Patient Name",
        "Phone",
        "Medicaid #",
        "DOB",
        "Pick-up Address",
        "Pick-up City",
        "Pick-up State",
        "Pick-up ZIP",
        "Drop-off Address",
        "Drop-off City",
        "Drop-off State",
        "Drop-off ZIP",
        "Appt Date",
        "Appt Time",
        "Trip Type",
        "Wheelchair?",
        "Notes",
    ]


@pytest.fixture
def sample_row_data():
    """A single Excel row matching sample_mapping columns."""
    return {
        "Patient Name": "Alice Wonderland",
        "Phone": "305-555-9876",
        "Medicaid #": "MCD444555666",
        "DOB": "03/15/1960",
        "Pick-up Address": "100 NW 1st Ave",
        "Pick-up City": "Miami",
        "Pick-up State": "FL",
        "Pick-up ZIP": "33101",
        "Drop-off Address": "200 SW 2nd St",
        "Drop-off City": "Miami",
        "Drop-off State": "FL",
        "Drop-off ZIP": "33130",
        "Appt Date": "2025-06-15",
        "Appt Time": "10:30",
        "Trip Type": "Round Trip",
        "Wheelchair?": "No",
        "Notes": "Needs walker",
    }


# ---------------------------------------------------------------------------
# ParseResult fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def successful_parse_result(sample_trip):
    """A ParseResult representing a successful parse."""
    return ParseResult(
        success=True,
        clinic_id="test_clinic",
        trips=[sample_trip],
        total_rows=1,
        successful_rows=1,
        failed_rows=0,
    )


# ---------------------------------------------------------------------------
# Database fixtures (in-memory SQLite)
# ---------------------------------------------------------------------------

@pytest.fixture
def db_url():
    """In-memory SQLite URL."""
    return "sqlite:///:memory:"


@pytest.fixture
def mapping_repo(db_url):
    return MappingRepository(db_url)


@pytest.fixture
def trip_repo(db_url):
    return TripRepository(db_url)


@pytest.fixture
def upload_repo(db_url):
    return UploadHistoryRepository(db_url)


# ---------------------------------------------------------------------------
# Temporary Excel file helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_excel_file(sample_excel_columns, tmp_path):
    """Create a temporary Excel file with sample data."""
    import pandas as pd

    data = {
        "Patient Name": ["Jane Doe", "John Smith"],
        "Phone": ["3055551234", "4075559876"],
        "Medicaid #": ["MCD111", "MCD222"],
        "DOB": ["01/15/1960", "06/20/1975"],
        "Pick-up Address": ["100 NW 1st Ave", "200 E Colonial Dr"],
        "Pick-up City": ["Miami", "Orlando"],
        "Pick-up State": ["FL", "FL"],
        "Pick-up ZIP": ["33101", "32801"],
        "Drop-off Address": ["200 SW 2nd St", "300 S Orange Ave"],
        "Drop-off City": ["Miami", "Orlando"],
        "Drop-off State": ["FL", "FL"],
        "Drop-off ZIP": ["33130", "32801"],
        "Appt Date": ["2025-06-15", "2025-06-16"],
        "Appt Time": ["10:30", "14:00"],
        "Trip Type": ["Round Trip", "One Way"],
        "Wheelchair?": ["No", "Yes"],
        "Notes": ["Walker needed", ""],
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "test_trips.xlsx"
    df.to_excel(str(file_path), index=False)
    return file_path


@pytest.fixture
def empty_excel_file(tmp_path):
    """Create an empty Excel file (headers only, no rows)."""
    import pandas as pd

    df = pd.DataFrame(columns=["Patient Name", "Medicaid #", "Pick-up Address"])
    file_path = tmp_path / "empty.xlsx"
    df.to_excel(str(file_path), index=False)
    return file_path
