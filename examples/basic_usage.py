"""
Basic Usage Example for NEMT Trip Parser

This shows how to use the parser in your existing website backend.
"""

from nemt_parser import TripParser, MappingRepository, TripRepository
from pathlib import Path


def example_1_first_time_clinic():
    """
    Example: Processing Excel from a clinic for the first time.

    The parser will suggest a column mapping that you review and save.
    """
    print("=== Example 1: First-time clinic upload ===\n")

    # Initialize with database
    mapping_repo = MappingRepository("sqlite:///nemt_trips.db")
    parser = TripParser(mapping_repository=mapping_repo)

    # Parse file from new clinic
    result = parser.parse_excel(
        file_path="sample_data/clinic_a_trips.xlsx",
        clinic_id="miami_medical",
        clinic_name="Miami Medical Center"
    )

    if result.needs_mapping:
        print("🔍 First time upload - mapping needed!")
        print(f"Detected columns: {result.detected_columns}\n")

        # Show suggested mapping
        mapping = result.suggested_mapping
        print("Suggested mapping:")
        print(f"  Patient Name: '{mapping.patient_name}'")
        print(f"  Medicaid ID: '{mapping.medicaid_id}'")
        print(f"  Pickup Address: '{mapping.pickup_address}'")
        print(f"  Appointment Date: '{mapping.appointment_date}'")
        print("  ... etc\n")

        # Review looks good? Save it!
        if parser.save_mapping(mapping):
            print("✅ Mapping saved! Future uploads will use this automatically.\n")

    if result.success:
        print(f"✅ Parsed {result.successful_rows} trips successfully")
        print(f"First trip: {result.trips[0].patient_name} on {result.trips[0].appointment_date}")
    else:
        print(f"❌ Errors: {result.errors}")


def example_2_returning_clinic():
    """
    Example: Processing Excel from a clinic with saved mapping.

    Automatic processing - no manual mapping needed!
    """
    print("\n=== Example 2: Returning clinic upload ===\n")

    mapping_repo = MappingRepository("sqlite:///nemt_trips.db")
    trip_repo = TripRepository("sqlite:///nemt_trips.db")
    parser = TripParser(mapping_repository=mapping_repo)

    # Parse file - mapping loads automatically
    result = parser.parse_excel(
        file_path="sample_data/clinic_a_trips_week2.xlsx",
        clinic_id="miami_medical"
    )

    if result.success:
        print(f"✅ Parsed {result.successful_rows} trips")

        # Save to database
        saved_count = trip_repo.save_trips(result.trips)
        print(f"💾 Saved {saved_count} trips to database")

        # Show sample trip
        trip = result.trips[0]
        print(f"\nExample trip:")
        print(f"  Patient: {trip.patient_name}")
        print(f"  From: {trip.pickup_address}, {trip.pickup_city}")
        print(f"  To: {trip.dropoff_address}, {trip.dropoff_city}")
        print(f"  Date: {trip.appointment_date} at {trip.appointment_time}")
        print(f"  Wheelchair: {'Yes' if trip.wheelchair else 'No'}")
    else:
        print(f"❌ Errors: {result.errors}")


def example_3_integrate_with_web_upload():
    """
    Example: Integration with your existing web upload handler.

    This is how you'd call it from your Flask/Django/FastAPI upload endpoint.
    """
    print("\n=== Example 3: Web integration ===\n")

    def handle_file_upload(file_path: str, clinic_id: str, user_id: str = None):
        """
        Your existing upload handler - just add parser integration!

        Args:
            file_path: Path to uploaded Excel file
            clinic_id: ID of the clinic uploading
            user_id: Optional ID of user who uploaded
        """
        # Initialize parser
        mapping_repo = MappingRepository("sqlite:///nemt_trips.db")
        trip_repo = TripRepository("sqlite:///nemt_trips.db")
        parser = TripParser(mapping_repository=mapping_repo)

        # Validate file first
        is_valid, error_msg = parser.validate_excel_file(file_path)
        if not is_valid:
            return {"success": False, "error": error_msg}

        # Parse the file
        result = parser.parse_excel(file_path=file_path, clinic_id=clinic_id)

        # First-time clinic?
        if result.needs_mapping:
            return {
                "success": False,
                "needs_mapping": True,
                "detected_columns": result.detected_columns,
                "suggested_mapping": result.suggested_mapping.model_dump(),
                "message": "Please review and confirm the column mapping"
            }

        # Parse successful?
        if result.success:
            # Save trips to database
            saved_count = trip_repo.save_trips(result.trips)

            return {
                "success": True,
                "trips_parsed": result.successful_rows,
                "trips_saved": saved_count,
                "warnings": result.warnings if result.warnings else []
            }
        else:
            return {
                "success": False,
                "errors": result.errors,
                "warnings": result.warnings
            }

    # Simulate upload
    response = handle_file_upload(
        file_path="sample_data/clinic_b_trips.xlsx",
        clinic_id="orlando_clinic",
        user_id="admin"
    )

    print(f"Upload response: {response}")


def example_4_custom_mapping_adjustment():
    """
    Example: Manually adjusting a suggested mapping.

    Sometimes the auto-detection isn't perfect - you can fix it!
    """
    print("\n=== Example 4: Adjust mapping ===\n")

    mapping_repo = MappingRepository("sqlite:///nemt_trips.db")
    parser = TripParser(mapping_repository=mapping_repo)

    result = parser.parse_excel(
        file_path="sample_data/clinic_c_trips.xlsx",
        clinic_id="tampa_clinic",
        clinic_name="Tampa General Hospital"
    )

    if result.needs_mapping:
        mapping = result.suggested_mapping

        # Maybe the auto-detection got something wrong...
        print("Auto-detected mappings:")
        print(f"  Wheelchair: '{mapping.wheelchair}'")

        # Fix it manually
        mapping.wheelchair = "WC Required"  # Correct column name
        mapping.notes = "Special Notes"  # Add a field that wasn't detected

        print("\nAdjusted mappings:")
        print(f"  Wheelchair: '{mapping.wheelchair}'")
        print(f"  Notes: '{mapping.notes}'")

        # Save the corrected mapping
        parser.save_mapping(mapping)
        print("\n✅ Corrected mapping saved!")


def example_5_list_clinics():
    """
    Example: List all clinics with saved mappings.

    Useful for admin dashboards.
    """
    print("\n=== Example 5: List all clinics ===\n")

    mapping_repo = MappingRepository("sqlite:///nemt_trips.db")
    parser = TripParser(mapping_repository=mapping_repo)

    clinics = parser.list_clinics()

    print(f"Total clinics with mappings: {len(clinics)}")
    for clinic in clinics:
        print(f"  • {clinic['clinic_name']} (ID: {clinic['clinic_id']})")
        print(f"    Last updated: {clinic['updated_at']}")


if __name__ == "__main__":
    # Run examples
    # Note: These will fail without actual Excel files - see next example
    # for creating sample data

    print("NEMT Trip Parser - Usage Examples")
    print("=" * 50)

    # Uncomment to run examples:
    # example_1_first_time_clinic()
    # example_2_returning_clinic()
    example_3_integrate_with_web_upload()
    # example_4_custom_mapping_adjustment()
    # example_5_list_clinics()

    print("\n" + "=" * 50)
    print("✅ Examples completed!")
