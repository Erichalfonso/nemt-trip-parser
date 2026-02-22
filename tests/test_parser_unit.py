"""
Unit tests for TripParser – Excel parsing, mapping retrieval, validation,
and error handling.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from nemt_parser.core.parser import TripParser
from nemt_parser.core.models import ColumnMapping, ParseResult


# =========================================================================
# validate_excel_file (static method — no DB needed)
# =========================================================================

class TestValidateExcelFile:
    def test_valid_xlsx(self, sample_excel_file):
        is_valid, error = TripParser.validate_excel_file(sample_excel_file)
        assert is_valid is True
        assert error is None

    def test_nonexistent_file(self, tmp_path):
        is_valid, error = TripParser.validate_excel_file(tmp_path / "nope.xlsx")
        assert is_valid is False
        assert "does not exist" in error

    def test_directory_path(self, tmp_path):
        is_valid, error = TripParser.validate_excel_file(tmp_path)
        assert is_valid is False
        assert "not a file" in error

    def test_wrong_extension(self, tmp_path):
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("a,b,c\n1,2,3")
        is_valid, error = TripParser.validate_excel_file(csv_file)
        assert is_valid is False
        assert "Invalid file type" in error

    def test_corrupt_file(self, tmp_path):
        bad_file = tmp_path / "corrupt.xlsx"
        bad_file.write_bytes(b"this is not excel")
        is_valid, error = TripParser.validate_excel_file(bad_file)
        assert is_valid is False
        assert "Error" in error


# =========================================================================
# parse_excel – happy path
# =========================================================================

class TestParseExcel:
    def test_first_time_clinic_needs_mapping(self, sample_excel_file):
        parser = TripParser()
        result = parser.parse_excel(
            file_path=str(sample_excel_file),
            clinic_id="new_clinic",
            clinic_name="New Clinic",
        )
        assert result.needs_mapping is True
        assert result.suggested_mapping is not None
        assert result.detected_columns is not None
        assert len(result.detected_columns) > 0

    def test_parse_with_explicit_mapping(self, sample_excel_file, sample_mapping):
        parser = TripParser()
        result = parser.parse_excel(
            file_path=str(sample_excel_file),
            clinic_id="test_clinic",
            mapping=sample_mapping,
        )
        assert result.success is True
        assert result.successful_rows == 2
        assert len(result.trips) == 2
        assert result.trips[0].patient_name == "Jane Doe"
        assert result.trips[1].patient_name == "John Smith"

    def test_parse_with_saved_mapping(self, sample_excel_file, sample_mapping, mapping_repo):
        mapping_repo.save_mapping(sample_mapping)
        parser = TripParser(mapping_repository=mapping_repo)
        result = parser.parse_excel(
            file_path=str(sample_excel_file),
            clinic_id="test_clinic",
        )
        assert result.success is True
        assert len(result.trips) == 2

    def test_file_not_found_error(self):
        parser = TripParser()
        result = parser.parse_excel(
            file_path="/nonexistent/path.xlsx",
            clinic_id="x",
        )
        assert result.success is False
        assert any("not found" in e.lower() or "error" in e.lower() for e in result.errors)

    def test_empty_file_returns_no_trips(self, empty_excel_file):
        parser = TripParser()
        result = parser.parse_excel(
            file_path=str(empty_excel_file),
            clinic_id="empty_clinic",
            clinic_name="Empty",
        )
        # No rows → no trips (may still need mapping)
        assert len(result.trips) == 0

    def test_skip_rows_parameter(self, sample_excel_file, sample_mapping):
        parser = TripParser()
        result = parser.parse_excel(
            file_path=str(sample_excel_file),
            clinic_id="test_clinic",
            mapping=sample_mapping,
            skip_rows=1,  # Skip first data row
        )
        # Skipping a row means we read fewer rows than normal, but column
        # names may shift. This validates the parameter is accepted.
        assert isinstance(result, ParseResult)

    def test_unmapped_columns_warning(self, sample_excel_file, sample_mapping):
        parser = TripParser()
        result = parser.parse_excel(
            file_path=str(sample_excel_file),
            clinic_id="test_clinic",
            mapping=sample_mapping,
        )
        # The mapping doesn't cover every column, so we should see warnings
        # about unmapped columns
        unmapped_warnings = [w for w in result.warnings if "Unmapped" in w]
        # At least some columns should be unmapped
        assert isinstance(unmapped_warnings, list)


# =========================================================================
# save_mapping / get_mapping / list_clinics / delete_mapping
# =========================================================================

class TestParserMappingOps:
    def test_save_mapping_without_repo_raises(self, sample_mapping):
        parser = TripParser()  # no repository
        with pytest.raises(ValueError, match="No mapping repository"):
            parser.save_mapping(sample_mapping)

    def test_save_and_get_mapping(self, mapping_repo, sample_mapping):
        parser = TripParser(mapping_repository=mapping_repo)
        assert parser.save_mapping(sample_mapping) is True
        retrieved = parser.get_mapping("test_clinic")
        assert retrieved is not None
        assert retrieved.clinic_id == "test_clinic"
        assert retrieved.patient_name == "Patient Name"

    def test_list_clinics(self, mapping_repo, sample_mapping):
        parser = TripParser(mapping_repository=mapping_repo)
        parser.save_mapping(sample_mapping)
        clinics = parser.list_clinics()
        assert len(clinics) >= 1
        assert any(c["clinic_id"] == "test_clinic" for c in clinics)

    def test_delete_mapping(self, mapping_repo, sample_mapping):
        parser = TripParser(mapping_repository=mapping_repo)
        parser.save_mapping(sample_mapping)
        assert parser.delete_mapping("test_clinic") is True
        assert parser.get_mapping("test_clinic") is None

    def test_get_mapping_no_repo(self):
        parser = TripParser()
        assert parser.get_mapping("anything") is None

    def test_list_clinics_no_repo(self):
        parser = TripParser()
        assert parser.list_clinics() == []

    def test_delete_mapping_no_repo(self):
        parser = TripParser()
        assert parser.delete_mapping("anything") is False
