"""
Unit tests for service_type_id mapping across all parser paths.

Ensures wheelchair=7, stretcher=9, ambulatory=1 in every code path.
"""

import pytest
from unittest.mock import MagicMock
from datetime import date, time


# === Tests for parse_smart_llm.determine_service_type ===

from parse_smart_llm import determine_service_type as smart_llm_service_type


class TestSmartLlmServiceType:
    def test_wheelchair(self):
        assert smart_llm_service_type("wheelchair") == 7

    def test_wheelchair_abbreviation_wc(self):
        assert smart_llm_service_type("wc") == 7

    def test_wheelchair_abbreviation_w_c(self):
        assert smart_llm_service_type("w/c") == 7

    def test_wheelchair_mixed_case(self):
        assert smart_llm_service_type("Wheelchair needed") == 7

    def test_stretcher(self):
        assert smart_llm_service_type("stretcher") == 9

    def test_gurney(self):
        assert smart_llm_service_type("gurney") == 9

    def test_stretcher_misspelling(self):
        assert smart_llm_service_type("strech") == 9

    def test_ambulatory_default(self):
        assert smart_llm_service_type("ambulatory") == 1

    def test_none_defaults_ambulatory(self):
        assert smart_llm_service_type(None) == 1

    def test_empty_string_defaults_ambulatory(self):
        assert smart_llm_service_type("") == 1

    def test_random_text_defaults_ambulatory(self):
        assert smart_llm_service_type("patient walks fine") == 1


# === Tests for parse_messy_clinic.determine_service_type ===

from parse_messy_clinic import determine_service_type as messy_clinic_service_type


class TestMessyClinicServiceType:
    def test_wheelchair(self):
        assert messy_clinic_service_type("wheelchair") == 7

    def test_wheelchair_abbreviation(self):
        assert messy_clinic_service_type("wc") == 7

    def test_wheelchair_in_notes(self):
        assert messy_clinic_service_type("Patient needs wheelchair assistance") == 7

    def test_stretcher(self):
        assert messy_clinic_service_type("stretcher") == 9

    def test_gurney(self):
        assert messy_clinic_service_type("gurney") == 9

    def test_ambulatory_default(self):
        assert messy_clinic_service_type("walks independently") == 1

    def test_none_defaults_ambulatory(self):
        assert messy_clinic_service_type(None) == 1

    def test_empty_string_defaults_ambulatory(self):
        assert messy_clinic_service_type("") == 1


# === Tests for output_schema.convert_to_output_format ===

from nemt_parser.core.output_schema import convert_to_output_format


def _make_trip(wheelchair=False, stretcher=False, ambulatory=True):
    """Create a mock Trip object with the required fields."""
    trip = MagicMock()
    trip.wheelchair = wheelchair
    trip.stretcher = stretcher
    trip.ambulatory = ambulatory
    trip.patient_name = "Test Patient"
    trip.patient_phone = "3051234567"
    trip.pickup_address = "123 Main St"
    trip.pickup_city = "Miami"
    trip.pickup_state = "FL"
    trip.pickup_zip = "33101"
    trip.dropoff_address = "456 Hospital Blvd"
    trip.dropoff_city = "Miami"
    trip.dropoff_state = "FL"
    trip.dropoff_zip = "33125"
    trip.appointment_date = date(2025, 1, 15)
    trip.appointment_time = time(9, 0)
    trip.notes = None
    trip.trip_type = MagicMock()
    trip.trip_type.value = "one_way"
    return trip


class TestOutputSchemaServiceType:
    def test_ambulatory(self):
        trip = _make_trip(wheelchair=False, stretcher=False)
        output = convert_to_output_format(trip)
        assert output.service_type_id == 1

    def test_wheelchair(self):
        trip = _make_trip(wheelchair=True, stretcher=False)
        output = convert_to_output_format(trip)
        assert output.service_type_id == 7

    def test_stretcher(self):
        trip = _make_trip(wheelchair=False, stretcher=True)
        output = convert_to_output_format(trip)
        assert output.service_type_id == 9

    def test_stretcher_takes_priority_over_wheelchair(self):
        trip = _make_trip(wheelchair=True, stretcher=True)
        output = convert_to_output_format(trip)
        assert output.service_type_id == 9


# === Cross-path consistency tests ===

class TestServiceTypeConsistency:
    """Verify all three code paths return the same IDs."""

    def test_all_paths_agree_on_wheelchair(self):
        smart = smart_llm_service_type("wheelchair")
        messy = messy_clinic_service_type("wheelchair")
        schema = convert_to_output_format(_make_trip(wheelchair=True)).service_type_id
        assert smart == messy == schema == 7

    def test_all_paths_agree_on_stretcher(self):
        smart = smart_llm_service_type("stretcher")
        messy = messy_clinic_service_type("stretcher")
        schema = convert_to_output_format(_make_trip(stretcher=True)).service_type_id
        assert smart == messy == schema == 9

    def test_all_paths_agree_on_ambulatory(self):
        smart = smart_llm_service_type(None)
        messy = messy_clinic_service_type(None)
        schema = convert_to_output_format(_make_trip()).service_type_id
        assert smart == messy == schema == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
