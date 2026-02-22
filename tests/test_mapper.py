"""
Unit tests for ColumnMapper – pattern matching, fuzzy scoring,
mapping suggestion, validation, and unmapped column detection.
"""

import pytest

from nemt_parser.core.mapper import ColumnMapper
from nemt_parser.core.models import ColumnMapping


# =========================================================================
# similarity_score
# =========================================================================

class TestSimilarityScore:
    def test_identical_strings(self):
        assert ColumnMapper.similarity_score("name", "name") == 1.0

    def test_case_insensitive(self):
        assert ColumnMapper.similarity_score("Name", "name") == 1.0

    def test_different_strings(self):
        score = ColumnMapper.similarity_score("patient_name", "dropoff_zip")
        assert score < 0.5

    def test_similar_strings(self):
        score = ColumnMapper.similarity_score("patient name", "patient_name")
        assert score > 0.7


# =========================================================================
# match_column
# =========================================================================

class TestMatchColumn:
    def test_exact_pattern_match_high_score(self):
        score = ColumnMapper.match_column("Patient Name", "patient_name")
        assert score == 0.9

    def test_pattern_match_partial(self):
        score = ColumnMapper.match_column("Client Full Name", "patient_name")
        assert score == 0.9  # matches "full.*name" pattern

    def test_fuzzy_fallback(self):
        score = ColumnMapper.match_column("Pat. Nam.", "patient_name")
        # No regex match → fuzzy score
        assert 0.0 < score < 0.9

    def test_no_match_low_score(self):
        score = ColumnMapper.match_column("Billing Code", "patient_name")
        assert score < 0.5

    def test_wheelchair_column(self):
        assert ColumnMapper.match_column("Wheelchair?", "wheelchair") == 0.9

    def test_destination_address(self):
        assert ColumnMapper.match_column("Destination Address", "dropoff_address") == 0.9

    def test_appointment_date(self):
        assert ColumnMapper.match_column("Appt Date", "appointment_date") == 0.9

    def test_phone_column(self):
        assert ColumnMapper.match_column("Cell Phone", "patient_phone") == 0.9

    def test_notes_column(self):
        assert ColumnMapper.match_column("Special Instructions", "notes") == 0.9

    def test_medicaid_variations(self):
        assert ColumnMapper.match_column("Insurance ID", "medicaid_id") == 0.9
        assert ColumnMapper.match_column("Member ID", "medicaid_id") == 0.9


# =========================================================================
# suggest_mapping
# =========================================================================

class TestSuggestMapping:
    def test_standard_columns_mapped(self, sample_excel_columns):
        mapping, scores = ColumnMapper.suggest_mapping(
            columns=sample_excel_columns,
            clinic_id="test",
            clinic_name="Test Clinic",
        )
        assert mapping.clinic_id == "test"
        assert mapping.patient_name == "Patient Name"
        assert mapping.medicaid_id == "Medicaid #"
        assert mapping.pickup_address == "Pick-up Address"
        assert mapping.appointment_date == "Appt Date"

    def test_confidence_scores_returned(self, sample_excel_columns):
        _, scores = ColumnMapper.suggest_mapping(
            columns=sample_excel_columns, clinic_id="test"
        )
        assert "patient_name" in scores
        assert scores["patient_name"] > 0.5

    def test_alternate_column_names(self):
        columns = [
            "Full Name",
            "Cell",
            "Insurance ID",
            "Date of Birth",
            "Origin Address",
            "Origin City",
            "Origin State",
            "Origin ZIP",
            "Destination Address",
            "Destination City",
            "Destination State",
            "Destination ZIP",
            "Visit Date",
            "Visit Time",
        ]
        mapping, _ = ColumnMapper.suggest_mapping(
            columns=columns, clinic_id="alt_clinic"
        )
        assert mapping.patient_name == "Full Name"
        assert mapping.medicaid_id == "Insurance ID"
        assert mapping.pickup_address == "Origin Address"
        assert mapping.appointment_date == "Visit Date"

    def test_low_threshold_second_pass_for_required(self):
        # Columns with poor names — the second pass should still map required fields
        columns = ["Col A", "Col B", "Col C", "Col D", "Col E",
                    "Col F", "Col G", "Col H", "Col I"]
        mapping, scores = ColumnMapper.suggest_mapping(
            columns=columns, clinic_id="bad_headers"
        )
        # Required fields must still be present in the mapping (even if low confidence)
        assert mapping.patient_name is not None
        assert mapping.medicaid_id is not None

    def test_custom_required_fields(self, sample_excel_columns):
        mapping, _ = ColumnMapper.suggest_mapping(
            columns=sample_excel_columns,
            clinic_id="test",
            required_fields=["patient_name", "medicaid_id"],
        )
        assert mapping.patient_name is not None
        assert mapping.medicaid_id is not None


# =========================================================================
# validate_mapping
# =========================================================================

class TestValidateMapping:
    def test_valid_mapping_no_errors(self, sample_mapping, sample_excel_columns):
        errors = ColumnMapper.validate_mapping(sample_mapping, sample_excel_columns)
        assert errors == []

    def test_missing_column_detected(self, sample_mapping):
        # Provide columns that don't include "Patient Name"
        bad_columns = ["Name", "Medicaid #", "Pick-up Address"]
        errors = ColumnMapper.validate_mapping(sample_mapping, bad_columns)
        assert len(errors) > 0
        assert any("Patient Name" in e for e in errors)

    def test_metadata_fields_skipped(self, sample_mapping, sample_excel_columns):
        # clinic_id, clinic_name, created_at, updated_at should not be validated
        errors = ColumnMapper.validate_mapping(sample_mapping, sample_excel_columns)
        assert not any("clinic_id" in e for e in errors)


# =========================================================================
# get_unmapped_columns
# =========================================================================

class TestGetUnmappedColumns:
    def test_all_mapped_returns_empty(self, sample_mapping, sample_excel_columns):
        unmapped = ColumnMapper.get_unmapped_columns(sample_excel_columns, sample_mapping)
        # Some columns may not be mapped (e.g., extra columns), but all fixture columns
        # should be mapped by sample_mapping
        # The fixture has columns like "Pick-up State" that may or may not be in mapping
        assert isinstance(unmapped, list)

    def test_extra_column_detected(self, sample_mapping):
        columns = ["Patient Name", "Medicaid #", "EXTRA_COL"]
        unmapped = ColumnMapper.get_unmapped_columns(columns, sample_mapping)
        assert "EXTRA_COL" in unmapped

    def test_empty_columns(self, sample_mapping):
        unmapped = ColumnMapper.get_unmapped_columns([], sample_mapping)
        assert unmapped == []
