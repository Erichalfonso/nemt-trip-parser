"""
Test the parser with YOUR exact JSON output format
"""

from nemt_parser import TripParser, MappingRepository
from nemt_parser.core.output_schema import convert_to_output_format
from pathlib import Path
import json


def test_your_output_format():
    print("=" * 80)
    print("TESTING YOUR EXACT JSON OUTPUT FORMAT")
    print("=" * 80)
    print()

    # Initialize parser
    db_path = "sqlite:///test_output_format.db"
    mapping_repo = MappingRepository(db_path)
    parser = TripParser(mapping_repository=mapping_repo)

    # Parse sample file
    sample_file = Path("sample_data/clinic_a_trips.xlsx")

    if not sample_file.exists():
        print("ERROR: Run 'python examples/create_sample_data.py' first")
        return

    print(f"Parsing: {sample_file}")
    print()

    result = parser.parse_excel(
        file_path=str(sample_file),
        clinic_id="test_clinic",
        clinic_name="Test Medical Center"
    )

    # Handle first-time mapping
    if result.needs_mapping:
        print("[First time clinic - saving mapping...]")
        parser.save_mapping(result.suggested_mapping)

        # Re-parse with saved mapping
        result = parser.parse_excel(
            file_path=str(sample_file),
            clinic_id="test_clinic"
        )

    if result.success:
        print(f"[OK] Successfully parsed {result.successful_rows} trips")
        print()
        print("=" * 80)
        print("SAMPLE OUTPUT (Your Exact Format):")
        print("=" * 80)
        print()

        # Convert first trip to your format
        if result.trips:
            trip = result.trips[0]
            output = convert_to_output_format(trip)

            # Print as JSON
            output_json = output.model_dump()
            print(json.dumps(output_json, indent=2))
            print()

        print("=" * 80)
        print("ALL TRIPS IN YOUR FORMAT:")
        print("=" * 80)
        print()

        # Convert all trips
        all_trips = [convert_to_output_format(trip).model_dump() for trip in result.trips]

        for i, trip in enumerate(all_trips, 1):
            print(f"Trip {i}:")
            print(f"  Passenger: {trip['passenger_name']}")
            print(f"  Phone: {trip['country_code']} {trip['passenger_phone']}")
            print(f"  From: {trip['source']}")
            print(f"  To: {trip['destination']}")
            print(f"  Pickup: {trip['pickup_date_time']}")
            print(f"  Appointment: {trip['appointment_time']}")
            print(f"  Service Type: {trip['service_type_id']} (1=ambulatory, 7=wheelchair, 9=stretcher)")
            print(f"  Return Trip: {trip['return_trip_needed']}")
            print()

        print("=" * 80)
        print("FULL JSON ARRAY (Ready to send to your system):")
        print("=" * 80)
        print()
        print(json.dumps(all_trips, indent=2))

    else:
        print("ERROR:")
        for error in result.errors:
            print(f"  - {error}")


def show_field_mapping():
    """Show how Excel fields map to your output format"""
    print("\n" + "=" * 80)
    print("FIELD MAPPING REFERENCE")
    print("=" * 80)
    print()
    print("Excel Column          →  Your JSON Field")
    print("-" * 80)
    print("Patient Name          →  passenger_name")
    print("Patient Phone         →  passenger_phone (digits only)")
    print("                      →  country_code (default: +1)")
    print("                      →  passenger_language (default: en)")
    print()
    print("Wheelchair? (Y/N)     →  service_type_id")
    print("                         1 = ambulatory (no wheelchair)")
    print("                         7 = wheelchair")
    print("                         9 = stretcher")
    print()
    print("Pick-up Address       →  source (combined full address)")
    print("Pick-up City          →  (included in source)")
    print("Pick-up ZIP           →  (included in source)")
    print("                      →  pickup_latitude (requires geocoding)")
    print("                      →  pickup_longitude (requires geocoding)")
    print()
    print("Drop-off Address      →  destination (combined full address)")
    print("Drop-off City         →  (included in destination)")
    print("Drop-off ZIP          →  (included in destination)")
    print("                      →  dropoff_latitude (requires geocoding)")
    print("                      →  dropoff_longitude (requires geocoding)")
    print()
    print("Appt Date + Time      →  appointment_time (YYYY-MM-DD HH:MM:SS)")
    print("                      →  pickup_date_time (YYYY-MM-DD HH:MM:SS)")
    print("                      →  eta_time (optional)")
    print()
    print("Notes                 →  special_note")
    print()
    print("Trip Type             →  return_trip_needed ('yes' or 'no')")
    print("(Round Trip/One Way)  →  return_trip_type ('immediate' or 'scheduled')")
    print()
    print("=" * 80)


if __name__ == "__main__":
    test_your_output_format()
    show_field_mapping()

    print("\n" + "=" * 80)
    print("[OK] TESTING COMPLETE!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. The API now returns data in YOUR exact format")
    print("  2. Start the API: python -m nemt_parser.integrations.flask_adapter")
    print("  3. Upload Excel file and get JSON in your format")
    print()
    print("NOTE: Geocoding (lat/lon) requires Google Maps API or similar service")
    print("      See nemt_parser/core/output_schema.py for integration instructions")
    print()
