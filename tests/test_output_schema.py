"""
Unit tests for output_schema – TripOutput conversion, address combination,
datetime formatting, service type mapping, and return trip logic.
"""

import pytest
from datetime import date, time

from nemt_parser.core.output_schema import (
    convert_to_output_format,
    convert_with_geocoding,
    geocode_address,
)
from nemt_parser.core.models import TripType


# =========================================================================
# Service type ID mapping
# =========================================================================

class TestServiceTypeId:
    def test_ambulatory(self, sample_trip):
        output = convert_to_output_format(sample_trip)
        assert output.service_type_id == 1

    def test_wheelchair(self, wheelchair_trip):
        output = convert_to_output_format(wheelchair_trip)
        assert output.service_type_id == 7

    def test_stretcher(self, stretcher_trip):
        output = convert_to_output_format(stretcher_trip)
        assert output.service_type_id == 9

    def test_stretcher_priority_over_wheelchair(self, sample_trip):
        trip = sample_trip.model_copy(update={"wheelchair": True, "stretcher": True})
        output = convert_to_output_format(trip)
        assert output.service_type_id == 9


# =========================================================================
# Address combination
# =========================================================================

class TestAddressCombination:
    def test_source_address_combined(self, sample_trip):
        output = convert_to_output_format(sample_trip)
        assert output.source == "100 NW 1st Ave, Miami, FL 33101"

    def test_destination_address_combined(self, sample_trip):
        output = convert_to_output_format(sample_trip)
        assert output.destination == "200 SW 2nd St, Miami, FL 33130"


# =========================================================================
# Phone number formatting
# =========================================================================

class TestPhoneFormatting:
    def test_phone_digits_only(self, sample_trip):
        output = convert_to_output_format(sample_trip)
        # "(305) 555-1234" → "3055551234"
        assert output.passenger_phone == "3055551234"

    def test_no_phone_returns_empty(self, minimal_trip):
        output = convert_to_output_format(minimal_trip)
        assert output.passenger_phone == ""


# =========================================================================
# Datetime formatting
# =========================================================================

class TestDatetimeFormatting:
    def test_appointment_time_format(self, sample_trip):
        output = convert_to_output_format(sample_trip)
        assert output.appointment_time == "2025-06-15 10:30:00"

    def test_pickup_date_time_format(self, sample_trip):
        output = convert_to_output_format(sample_trip)
        assert output.pickup_date_time == "2025-06-15 10:30:00"

    def test_no_time_defaults_midnight(self, minimal_trip):
        output = convert_to_output_format(minimal_trip)
        assert output.appointment_time == "2025-07-01 00:00:00"
        assert output.pickup_date_time == "2025-07-01 00:00:00"


# =========================================================================
# Return trip logic
# =========================================================================

class TestReturnTrip:
    def test_round_trip_returns_yes_immediate(self, sample_trip):
        assert sample_trip.trip_type == TripType.ROUND_TRIP
        output = convert_to_output_format(sample_trip)
        assert output.return_trip_needed == "yes"
        assert output.return_trip_type == "immediate"

    def test_return_type_returns_yes(self, sample_trip):
        trip = sample_trip.model_copy(update={"trip_type": TripType.RETURN})
        output = convert_to_output_format(trip)
        assert output.return_trip_needed == "yes"
        assert output.return_trip_type is None

    def test_pickup_only_returns_no(self, sample_trip):
        trip = sample_trip.model_copy(update={"trip_type": TripType.PICKUP})
        output = convert_to_output_format(trip)
        assert output.return_trip_needed == "no"
        assert output.return_trip_type is None


# =========================================================================
# Passenger defaults
# =========================================================================

class TestPassengerDefaults:
    def test_country_code_default(self, sample_trip):
        output = convert_to_output_format(sample_trip)
        assert output.country_code == "+1"

    def test_language_default(self, sample_trip):
        output = convert_to_output_format(sample_trip)
        assert output.passenger_language == "en"

    def test_passenger_name(self, sample_trip):
        output = convert_to_output_format(sample_trip)
        assert output.passenger_name == "Jane Doe"


# =========================================================================
# Notes / special_note
# =========================================================================

class TestSpecialNote:
    def test_notes_mapped(self, sample_trip):
        output = convert_to_output_format(sample_trip)
        assert output.special_note == "Needs walker assistance"

    def test_no_notes(self, minimal_trip):
        output = convert_to_output_format(minimal_trip)
        assert output.special_note is None


# =========================================================================
# GPS / geocoding placeholders
# =========================================================================

class TestGeocoding:
    def test_geocode_address_returns_none(self):
        lat, lon = geocode_address("123 Main St, Miami, FL 33101")
        assert lat is None
        assert lon is None

    def test_convert_with_geocoding_runs(self, sample_trip):
        output = convert_with_geocoding(sample_trip)
        # geocode_address returns (None, None) so coordinates stay None
        assert output.pickup_latitude is None
        assert output.pickup_longitude is None
        assert output.dropoff_latitude is None
        assert output.dropoff_longitude is None

    def test_eta_time_default_none(self, sample_trip):
        output = convert_to_output_format(sample_trip)
        assert output.eta_time is None
