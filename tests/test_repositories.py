"""
Unit tests for database repositories – MappingRepository, TripRepository,
and UploadHistoryRepository using in-memory SQLite.
"""

import pytest
from datetime import date, time, datetime

from nemt_parser.core.models import ColumnMapping, Trip, TripType, ParseResult
from nemt_parser.database.repositories import (
    MappingRepository,
    TripRepository,
    UploadHistoryRepository,
)


# =========================================================================
# MappingRepository
# =========================================================================

class TestMappingRepository:
    def test_save_and_retrieve(self, mapping_repo, sample_mapping):
        assert mapping_repo.save_mapping(sample_mapping) is True
        result = mapping_repo.get_mapping("test_clinic")
        assert result is not None
        assert result.clinic_id == "test_clinic"
        assert result.patient_name == "Patient Name"
        assert result.medicaid_id == "Medicaid #"

    def test_get_nonexistent_returns_none(self, mapping_repo):
        assert mapping_repo.get_mapping("no_such_clinic") is None

    def test_update_existing_mapping(self, mapping_repo, sample_mapping):
        mapping_repo.save_mapping(sample_mapping)
        updated = sample_mapping.model_copy(update={"patient_name": "Full Name"})
        mapping_repo.save_mapping(updated)
        result = mapping_repo.get_mapping("test_clinic")
        assert result.patient_name == "Full Name"

    def test_list_clinics_empty(self, mapping_repo):
        assert mapping_repo.list_clinics() == []

    def test_list_clinics_after_save(self, mapping_repo, sample_mapping):
        mapping_repo.save_mapping(sample_mapping)
        clinics = mapping_repo.list_clinics()
        assert len(clinics) == 1
        assert clinics[0]["clinic_id"] == "test_clinic"

    def test_list_multiple_clinics(self, mapping_repo, sample_mapping):
        mapping_repo.save_mapping(sample_mapping)
        second = sample_mapping.model_copy(
            update={"clinic_id": "clinic_b", "clinic_name": "Clinic B"}
        )
        mapping_repo.save_mapping(second)
        clinics = mapping_repo.list_clinics()
        assert len(clinics) == 2

    def test_delete_mapping(self, mapping_repo, sample_mapping):
        mapping_repo.save_mapping(sample_mapping)
        assert mapping_repo.delete_mapping("test_clinic") is True
        assert mapping_repo.get_mapping("test_clinic") is None

    def test_delete_nonexistent_returns_false(self, mapping_repo):
        assert mapping_repo.delete_mapping("ghost") is False


# =========================================================================
# TripRepository
# =========================================================================

class TestTripRepository:
    def test_save_trips(self, trip_repo, sample_trip):
        count = trip_repo.save_trips([sample_trip])
        assert count == 1

    def test_save_multiple_trips(self, trip_repo, sample_trip, minimal_trip):
        count = trip_repo.save_trips([sample_trip, minimal_trip])
        assert count == 2

    def test_save_empty_list(self, trip_repo):
        count = trip_repo.save_trips([])
        assert count == 0

    def test_get_trips_by_clinic(self, trip_repo, sample_trip):
        trip_repo.save_trips([sample_trip])
        trips = trip_repo.get_trips_by_clinic("test_clinic")
        assert len(trips) >= 1
        assert trips[0].patient_name == "Jane Doe"

    def test_get_trips_by_clinic_no_match(self, trip_repo, sample_trip):
        trip_repo.save_trips([sample_trip])
        trips = trip_repo.get_trips_by_clinic("other_clinic")
        assert len(trips) == 0

    def test_get_trips_by_date_range(self, trip_repo, sample_trip):
        trip_repo.save_trips([sample_trip])
        trips = trip_repo.get_trips_by_date_range(
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 30),
        )
        assert len(trips) >= 1

    def test_get_trips_by_date_range_no_match(self, trip_repo, sample_trip):
        trip_repo.save_trips([sample_trip])
        trips = trip_repo.get_trips_by_date_range(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )
        assert len(trips) == 0

    def test_get_trips_by_date_range_filtered_by_clinic(self, trip_repo, sample_trip):
        trip_repo.save_trips([sample_trip])
        trips = trip_repo.get_trips_by_date_range(
            start_date=date(2025, 6, 1),
            end_date=date(2025, 6, 30),
            clinic_id="test_clinic",
        )
        assert len(trips) >= 1

    def test_get_trips_by_clinic_limit(self, trip_repo, sample_trip):
        # Save several trips
        trips_to_save = [
            sample_trip.model_copy(update={"patient_name": f"Patient {i}"})
            for i in range(5)
        ]
        trip_repo.save_trips(trips_to_save)
        trips = trip_repo.get_trips_by_clinic("test_clinic", limit=2)
        assert len(trips) == 2


# =========================================================================
# UploadHistoryRepository
# =========================================================================

class TestUploadHistoryRepository:
    def test_log_upload(self, upload_repo, successful_parse_result):
        upload_id = upload_repo.log_upload(
            clinic_id="test_clinic",
            filename="test.xlsx",
            result=successful_parse_result,
            uploaded_by="user_1",
            file_size=1024,
        )
        assert upload_id > 0

    def test_get_upload_history(self, upload_repo, successful_parse_result):
        upload_repo.log_upload(
            clinic_id="test_clinic",
            filename="test.xlsx",
            result=successful_parse_result,
        )
        history = upload_repo.get_upload_history()
        assert len(history) == 1
        assert history[0].clinic_id == "test_clinic"
        assert history[0].filename == "test.xlsx"
        assert history[0].total_rows == 1

    def test_get_history_filtered_by_clinic(self, upload_repo, successful_parse_result):
        upload_repo.log_upload(
            clinic_id="clinic_a",
            filename="a.xlsx",
            result=successful_parse_result,
        )
        upload_repo.log_upload(
            clinic_id="clinic_b",
            filename="b.xlsx",
            result=successful_parse_result,
        )
        history = upload_repo.get_upload_history(clinic_id="clinic_a")
        assert len(history) == 1
        assert history[0].clinic_id == "clinic_a"

    def test_get_history_respects_limit(self, upload_repo, successful_parse_result):
        for i in range(5):
            upload_repo.log_upload(
                clinic_id="test",
                filename=f"file_{i}.xlsx",
                result=successful_parse_result,
            )
        history = upload_repo.get_upload_history(limit=3)
        assert len(history) == 3

    def test_upload_with_errors(self, upload_repo):
        result = ParseResult(
            success=False,
            clinic_id="bad_clinic",
            total_rows=10,
            successful_rows=5,
            failed_rows=5,
            errors=["Missing column: Patient Name"],
            warnings=["Row 3: invalid date"],
        )
        upload_id = upload_repo.log_upload(
            clinic_id="bad_clinic",
            filename="bad.xlsx",
            result=result,
        )
        assert upload_id > 0
        history = upload_repo.get_upload_history()
        assert history[0].failed_rows == 5
        assert history[0].errors is not None
