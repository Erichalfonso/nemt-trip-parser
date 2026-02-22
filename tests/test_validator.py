"""
Unit tests for DataValidator – date/time/boolean parsing, phone/zip cleaning,
and row_to_trip conversion.
"""

import pytest
from datetime import date, time, datetime

from nemt_parser.core.validator import DataValidator
from nemt_parser.core.models import TripType


# =========================================================================
# parse_date
# =========================================================================

class TestParseDate:
    def test_none_returns_none(self):
        assert DataValidator.parse_date(None) is None

    def test_empty_string_returns_none(self):
        assert DataValidator.parse_date("") is None

    def test_date_object_passthrough(self):
        d = date(2025, 1, 15)
        assert DataValidator.parse_date(d) == d

    def test_datetime_extracts_date(self):
        dt = datetime(2025, 1, 15, 10, 30)
        assert DataValidator.parse_date(dt) == date(2025, 1, 15)

    def test_iso_format(self):
        assert DataValidator.parse_date("2025-01-15") == date(2025, 1, 15)

    def test_us_format_mm_dd_yyyy(self):
        assert DataValidator.parse_date("01/15/2025") == date(2025, 1, 15)

    def test_us_format_short_year(self):
        assert DataValidator.parse_date("01/15/25") == date(2025, 1, 15)

    def test_compact_format_yyyymmdd(self):
        assert DataValidator.parse_date("20250115") == date(2025, 1, 15)

    def test_dash_format_mm_dd_yyyy(self):
        assert DataValidator.parse_date("01-15-2025") == date(2025, 1, 15)

    def test_whitespace_stripped(self):
        assert DataValidator.parse_date("  2025-01-15  ") == date(2025, 1, 15)

    def test_invalid_string_returns_none(self):
        assert DataValidator.parse_date("not-a-date") is None

    def test_excel_serial_date(self):
        # Excel serial 45658 = 2024-12-31 (approximately)
        result = DataValidator.parse_date("44927")  # 2023-01-01
        assert isinstance(result, date)

    def test_excel_serial_date_as_number(self):
        result = DataValidator.parse_date(44927)
        assert isinstance(result, date)


# =========================================================================
# parse_time
# =========================================================================

class TestParseTime:
    def test_none_returns_none(self):
        assert DataValidator.parse_time(None) is None

    def test_empty_string_returns_none(self):
        assert DataValidator.parse_time("") is None

    def test_time_object_passthrough(self):
        t = time(10, 30)
        assert DataValidator.parse_time(t) == t

    def test_datetime_extracts_time(self):
        dt = datetime(2025, 1, 15, 14, 45, 30)
        assert DataValidator.parse_time(dt) == time(14, 45, 30)

    def test_hh_mm_ss(self):
        assert DataValidator.parse_time("14:30:00") == time(14, 30, 0)

    def test_hh_mm(self):
        assert DataValidator.parse_time("14:30") == time(14, 30)

    def test_12h_format_am(self):
        assert DataValidator.parse_time("9:30 AM") == time(9, 30)

    def test_12h_format_pm(self):
        assert DataValidator.parse_time("2:30 PM") == time(14, 30)

    def test_12h_no_space(self):
        assert DataValidator.parse_time("2:30PM") == time(14, 30)

    def test_whitespace_stripped(self):
        assert DataValidator.parse_time("  10:30  ") == time(10, 30)

    def test_invalid_string_returns_none(self):
        assert DataValidator.parse_time("not-a-time") is None


# =========================================================================
# parse_boolean
# =========================================================================

class TestParseBoolean:
    @pytest.mark.parametrize("value", ["yes", "Yes", "YES", "y", "Y"])
    def test_yes_variants(self, value):
        assert DataValidator.parse_boolean(value) is True

    @pytest.mark.parametrize("value", ["true", "True", "TRUE"])
    def test_true_variants(self, value):
        assert DataValidator.parse_boolean(value) is True

    def test_string_one(self):
        assert DataValidator.parse_boolean("1") is True

    def test_x_marker(self):
        assert DataValidator.parse_boolean("x") is True

    @pytest.mark.parametrize("value", ["no", "No", "NO", "n", "N"])
    def test_no_variants(self, value):
        assert DataValidator.parse_boolean(value) is False

    @pytest.mark.parametrize("value", ["false", "False", "FALSE"])
    def test_false_variants(self, value):
        assert DataValidator.parse_boolean(value) is False

    def test_string_zero(self):
        assert DataValidator.parse_boolean("0") is False

    def test_empty_string(self):
        assert DataValidator.parse_boolean("") is False

    def test_python_bool_true(self):
        assert DataValidator.parse_boolean(True) is True

    def test_python_bool_false(self):
        assert DataValidator.parse_boolean(False) is False

    def test_int_one(self):
        assert DataValidator.parse_boolean(1) is True

    def test_int_zero(self):
        assert DataValidator.parse_boolean(0) is False

    def test_float_nonzero(self):
        assert DataValidator.parse_boolean(1.5) is True

    def test_none_returns_false(self):
        assert DataValidator.parse_boolean(None) is False

    def test_whitespace_stripped(self):
        assert DataValidator.parse_boolean("  yes  ") is True


# =========================================================================
# parse_trip_type
# =========================================================================

class TestParseTripType:
    def test_round_trip(self):
        assert DataValidator.parse_trip_type("Round Trip") == TripType.ROUND_TRIP

    def test_both_keyword(self):
        assert DataValidator.parse_trip_type("both ways") == TripType.ROUND_TRIP

    def test_return_trip(self):
        assert DataValidator.parse_trip_type("Return") == TripType.RETURN

    def test_dropoff_keyword(self):
        assert DataValidator.parse_trip_type("drop off only") == TripType.RETURN

    def test_pickup_keyword(self):
        assert DataValidator.parse_trip_type("Pickup Only") == TripType.PICKUP

    def test_pick_keyword(self):
        assert DataValidator.parse_trip_type("pick up") == TripType.PICKUP

    def test_trip_type_enum_passthrough(self):
        assert DataValidator.parse_trip_type(TripType.RETURN) == TripType.RETURN

    def test_default_is_round_trip(self):
        assert DataValidator.parse_trip_type("unknown") == TripType.ROUND_TRIP

    def test_none_defaults_round_trip(self):
        # None is not a string and not TripType → default
        assert DataValidator.parse_trip_type(None) == TripType.ROUND_TRIP


# =========================================================================
# clean_phone
# =========================================================================

class TestCleanPhone:
    def test_none_returns_none(self):
        assert DataValidator.clean_phone(None) is None

    def test_ten_digits_formatted(self):
        assert DataValidator.clean_phone("3055551234") == "(305) 555-1234"

    def test_strips_dashes(self):
        assert DataValidator.clean_phone("305-555-1234") == "(305) 555-1234"

    def test_strips_parens_and_spaces(self):
        assert DataValidator.clean_phone("(305) 555-1234") == "(305) 555-1234"

    def test_non_standard_length_returned_as_is(self):
        # 11 digits — not formatted
        result = DataValidator.clean_phone("13055551234")
        assert result == "13055551234"

    def test_empty_digits_returns_none(self):
        assert DataValidator.clean_phone("   ") is None

    def test_numeric_input(self):
        assert DataValidator.clean_phone(3055551234) == "(305) 555-1234"


# =========================================================================
# clean_zip
# =========================================================================

class TestCleanZip:
    def test_none_returns_empty(self):
        assert DataValidator.clean_zip(None) == ""

    def test_five_digit_zip(self):
        assert DataValidator.clean_zip("33101") == "33101"

    def test_zip_plus_four(self):
        assert DataValidator.clean_zip("33101-1234") == "33101-1234"

    def test_pads_short_zip(self):
        assert DataValidator.clean_zip("1234") == "01234"

    def test_strips_whitespace(self):
        assert DataValidator.clean_zip("  33101  ") == "33101"

    def test_numeric_input(self):
        assert DataValidator.clean_zip(33101) == "33101"

    def test_float_zip(self):
        # pandas can read ZIP as float "33101.0"
        assert DataValidator.clean_zip("33101.0") == "331010"  # strips non-numeric except dash


# =========================================================================
# row_to_trip
# =========================================================================

class TestRowToTrip:
    def test_valid_row_produces_trip(self, sample_mapping, sample_row_data):
        trip, errors = DataValidator.row_to_trip(
            sample_row_data, sample_mapping, source_clinic_id="test"
        )
        assert trip is not None
        assert errors == []
        assert trip.patient_name == "Alice Wonderland"
        assert trip.medicaid_id == "MCD444555666"
        assert trip.pickup_city == "Miami"
        assert trip.appointment_date == date(2025, 6, 15)

    def test_wheelchair_parsed_from_row(self, sample_mapping, sample_row_data):
        sample_row_data["Wheelchair?"] = "Yes"
        trip, _ = DataValidator.row_to_trip(sample_row_data, sample_mapping)
        assert trip.wheelchair is True

    def test_missing_column_uses_none(self, sample_mapping, sample_row_data):
        del sample_row_data["Notes"]
        trip, _ = DataValidator.row_to_trip(sample_row_data, sample_mapping)
        assert trip.notes is None

    def test_phone_cleaned_in_row(self, sample_mapping, sample_row_data):
        trip, _ = DataValidator.row_to_trip(sample_row_data, sample_mapping)
        assert trip.patient_phone == "(305) 555-9876"

    def test_default_state_fl(self, sample_mapping, sample_row_data):
        # Remove state from row data
        del sample_row_data["Pick-up State"]
        sample_mapping_no_state = sample_mapping.model_copy(update={"pickup_state": None})
        trip, _ = DataValidator.row_to_trip(sample_row_data, sample_mapping_no_state)
        assert trip.pickup_state == "FL"

    def test_trip_type_parsed(self, sample_mapping, sample_row_data):
        trip, _ = DataValidator.row_to_trip(sample_row_data, sample_mapping)
        assert trip.trip_type == TripType.ROUND_TRIP

    def test_source_clinic_id_set(self, sample_mapping, sample_row_data):
        trip, _ = DataValidator.row_to_trip(
            sample_row_data, sample_mapping, source_clinic_id="my_clinic"
        )
        assert trip.source_clinic_id == "my_clinic"
