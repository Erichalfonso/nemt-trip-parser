"""
Quick test of the NEMT parser with sample data.
"""

from nemt_parser import TripParser, MappingRepository, TripRepository
from pathlib import Path

def test_parser():
    print("=" * 70)
    print("NEMT TRIP PARSER - TEST")
    print("=" * 70)
    print()

    # Initialize repositories
    db_path = "sqlite:///test_nemt_trips.db"
    mapping_repo = MappingRepository(db_path)
    trip_repo = TripRepository(db_path)

    # Initialize parser
    parser = TripParser(mapping_repository=mapping_repo)

    # Test with Clinic A data
    print("[1] Testing with Clinic A (Miami Medical Center)")
    print("-" * 70)

    sample_file = Path("sample_data/clinic_a_trips.xlsx")

    if not sample_file.exists():
        print(f"ERROR: Sample file not found: {sample_file}")
        print("Run: python examples/create_sample_data.py first")
        return

    # Parse the file
    result = parser.parse_excel(
        file_path=str(sample_file),
        clinic_id="miami_medical",
        clinic_name="Miami Medical Center"
    )

    print(f"Detected columns: {', '.join(result.detected_columns[:5])}...")
    print()

    # Check if mapping needed
    if result.needs_mapping:
        print("[FIRST TIME CLINIC] Mapping suggestion:")
        print(f"  Patient Name column: '{result.suggested_mapping.patient_name}'")
        print(f"  Medicaid ID column: '{result.suggested_mapping.medicaid_id}'")
        print(f"  Pickup Address column: '{result.suggested_mapping.pickup_address}'")
        print(f"  Appointment Date column: '{result.suggested_mapping.appointment_date}'")
        print()

        # Save the mapping
        if parser.save_mapping(result.suggested_mapping):
            print("[OK] Mapping saved successfully!")
            print()

            # Re-parse with saved mapping
            print("[2] Re-parsing with saved mapping...")
            print("-" * 70)
            result = parser.parse_excel(
                file_path=str(sample_file),
                clinic_id="miami_medical"
            )

    # Show results
    if result.success:
        print(f"[SUCCESS] Parsed {result.successful_rows} trips")
        print()

        # Show first trip as JSON
        if result.trips:
            trip = result.trips[0]
            print("Sample trip (JSON format):")
            print("-" * 70)
            import json
            trip_json = trip.model_dump()
            # Convert date/time objects to strings for JSON
            trip_json['appointment_date'] = str(trip_json['appointment_date'])
            if trip_json['appointment_time']:
                trip_json['appointment_time'] = str(trip_json['appointment_time'])
            if trip_json['date_of_birth']:
                trip_json['date_of_birth'] = str(trip_json['date_of_birth'])
            if trip_json['uploaded_at']:
                trip_json['uploaded_at'] = trip_json['uploaded_at'].isoformat()

            print(json.dumps(trip_json, indent=2))
            print()

        # Save to database
        saved_count = trip_repo.save_trips(result.trips)
        print(f"[OK] Saved {saved_count} trips to database")
        print()

        # Show warnings if any
        if result.warnings:
            print("Warnings:")
            for warning in result.warnings[:3]:
                print(f"  - {warning}")
            print()

    else:
        print(f"[ERROR] Parsing failed:")
        for error in result.errors:
            print(f"  - {error}")
        print()

    # Test with Clinic B (different columns)
    print()
    print("[3] Testing with Clinic B (Orlando Clinic - different format)")
    print("-" * 70)

    sample_file_b = Path("sample_data/clinic_b_trips.xlsx")

    if sample_file_b.exists():
        result_b = parser.parse_excel(
            file_path=str(sample_file_b),
            clinic_id="orlando_clinic",
            clinic_name="Orlando Clinic"
        )

        print(f"Detected columns: {', '.join(result_b.detected_columns[:5])}...")
        print()

        if result_b.needs_mapping:
            print("[FIRST TIME] Column mapping suggested:")
            print(f"  'Full Name' -> patient_name")
            print(f"  'Insurance ID' -> medicaid_id")
            print(f"  'Origin Address' -> pickup_address")
            print(f"  'Destination Address' -> dropoff_address")
            print()

            # Save mapping
            parser.save_mapping(result_b.suggested_mapping)
            print("[OK] Mapping saved!")
            print()

            # Re-parse
            result_b = parser.parse_excel(
                file_path=str(sample_file_b),
                clinic_id="orlando_clinic"
            )

        print(f"[SUCCESS] Parsed {result_b.successful_rows} trips from Orlando Clinic")
        print()

    # Show all clinics
    print("[4] All clinics with saved mappings:")
    print("-" * 70)
    clinics = parser.list_clinics()
    for clinic in clinics:
        print(f"  - {clinic['clinic_name']} (ID: {clinic['clinic_id']})")
    print()

    print("=" * 70)
    print("TEST COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Check test_nemt_trips.db for saved data")
    print("  2. Run the Flask API: python -m nemt_parser.integrations.flask_adapter")
    print("  3. Test the API endpoints (see API_DOCUMENTATION.md)")
    print()


if __name__ == "__main__":
    try:
        test_parser()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
