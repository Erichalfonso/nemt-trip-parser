"""
Test YOUR Excel file with the parser
"""

from nemt_parser import TripParser, MappingRepository
from nemt_parser.core.output_schema import convert_to_output_format
import json

# ============================================================================
# EDIT THESE VALUES
# ============================================================================

# Path to YOUR Excel file
EXCEL_FILE = r"C:\Users\erich\Downloads\ppol_example_small_clinic_messy.xlsx"  # <-- CHANGE THIS

# Your clinic ID
CLINIC_ID = "clinic_1"  # <-- CHANGE THIS

# ============================================================================

def test_my_excel_file():
    print("=" * 80)
    print("TESTING YOUR EXCEL FILE")
    print("=" * 80)
    print()

    print(f"File: {EXCEL_FILE}")
    print(f"Clinic ID: {CLINIC_ID}")
    print()

    # Initialize parser
    # Using database to store mappings (so you don't have to map again next time)
    repo = MappingRepository("sqlite:///my_test.db")
    parser = TripParser(mapping_repository=repo)

    # NOTE: Trips are NOT saved to database - only returned as JSON!

    # Parse your file
    print("Parsing...")
    result = parser.parse_excel(
        file_path=EXCEL_FILE,
        clinic_id=CLINIC_ID
    )

    print()
    print("=" * 80)
    print("DETECTED COLUMNS:")
    print("=" * 80)
    for i, col in enumerate(result.detected_columns, 1):
        print(f"  {i}. {col}")
    print()

    # First time clinic?
    if result.needs_mapping:
        print("=" * 80)
        print("SUGGESTED COLUMN MAPPING:")
        print("=" * 80)
        mapping = result.suggested_mapping

        print(f"  Passenger Name:     '{mapping.patient_name}'")
        print(f"  Phone:              '{mapping.patient_phone}'")
        print(f"  Medicaid/Member ID: '{mapping.medicaid_id}'")
        print(f"  Pickup Address:     '{mapping.pickup_address}'")
        print(f"  Pickup City:        '{mapping.pickup_city}'")
        print(f"  Pickup ZIP:         '{mapping.pickup_zip}'")
        print(f"  Dropoff Address:    '{mapping.dropoff_address}'")
        print(f"  Dropoff City:       '{mapping.dropoff_city}'")
        print(f"  Dropoff ZIP:        '{mapping.dropoff_zip}'")
        print(f"  Appointment Date:   '{mapping.appointment_date}'")
        print(f"  Appointment Time:   '{mapping.appointment_time}'")
        print(f"  Wheelchair:         '{mapping.wheelchair}'")
        print(f"  Notes:              '{mapping.notes}'")
        print()

        # Ask user
        print("Does this mapping look correct? (y/n)")
        response = input("> ").strip().lower()

        if response == 'y':
            print("\nSaving mapping...")
            parser.save_mapping(mapping)
            print("[OK] Mapping saved!")
            print()

            # Re-parse with saved mapping
            print("Re-parsing with saved mapping...")
            result = parser.parse_excel(
                file_path=EXCEL_FILE,
                clinic_id=CLINIC_ID
            )

    # Show results
    if result.success:
        print("=" * 80)
        print(f"SUCCESS! Parsed {result.successful_rows} trips")
        print("=" * 80)
        print()

        if result.warnings:
            print("WARNINGS:")
            for warning in result.warnings:
                print(f"  - {warning}")
            print()

        # Convert to YOUR format and show
        print("=" * 80)
        print("SAMPLE OUTPUT (Your Format):")
        print("=" * 80)

        if result.trips:
            # First trip
            trip = result.trips[0]
            output = convert_to_output_format(trip)
            print(json.dumps(output.model_dump(), indent=2))
            print()

            # All trips
            print("=" * 80)
            print(f"ALL {len(result.trips)} TRIPS:")
            print("=" * 80)

            all_output = [convert_to_output_format(t).model_dump() for t in result.trips]

            for i, trip in enumerate(all_output, 1):
                print(f"\n{i}. {trip['passenger_name']}")
                print(f"   Phone: {trip['country_code']} {trip['passenger_phone']}")
                print(f"   From: {trip['source']}")
                print(f"   To: {trip['destination']}")
                print(f"   When: {trip['appointment_time']}")
                print(f"   Service: {trip['service_type_id']} (1=ambulatory, 2=wheelchair, 3=stretcher)")

            print()
            print("=" * 80)
            print("FULL JSON (Ready to use!):")
            print("=" * 80)
            print(json.dumps(all_output, indent=2))

    else:
        print("=" * 80)
        print("ERRORS:")
        print("=" * 80)
        for error in result.errors:
            print(f"  - {error}")
        print()


if __name__ == "__main__":
    print()
    print("*" * 80)
    print("IMPORTANT: Edit the file path and clinic ID at the top of this file first!")
    print("*" * 80)
    print()

    try:
        test_my_excel_file()
    except FileNotFoundError:
        print("\n[ERROR] File not found!")
        print(f"Looking for: {EXCEL_FILE}")
        print("\nPlease update the EXCEL_FILE path at the top of this script.")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
