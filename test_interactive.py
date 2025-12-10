"""
Interactive API Test Script for NEMT Trip Parser

Run this script and answer a few simple questions to test the parser with any Excel file.
"""

import requests
import json
import os
import sys
from pathlib import Path


# API Configuration
API_URL = "https://web-production-c09c8.up.railway.app/api/upload"
API_KEY = "REDACTED_API_KEY"


def validate_file(file_path):
    """
    Validate that file exists and is a valid Excel file.

    Returns:
        (is_valid: bool, error_message: str or None)
    """
    # Remove quotes if drag-dropped
    file_path = file_path.strip().strip('"').strip("'")

    path = Path(file_path)

    if not path.exists():
        return False, f"File not found: {file_path}"

    if not path.is_file():
        return False, f"Path is not a file: {file_path}"

    if path.suffix.lower() not in ['.xlsx', '.xls']:
        return False, f"Invalid file type: {path.suffix}. Expected .xlsx or .xls"

    return True, None


def prompt_yes_no(question, default=True):
    """
    Prompt user for yes/no answer.

    Args:
        question: Question to ask
        default: Default value if user presses Enter (True or False)

    Returns:
        bool
    """
    default_str = "[Y/n]" if default else "[y/N]"
    full_question = f"{question} {default_str}: "

    while True:
        response = input(full_question).strip().lower()

        if response == '':
            return default

        if response in ['y', 'yes']:
            return True

        if response in ['n', 'no']:
            return False

        print("Please enter 'y' or 'n' (or press Enter for default)")


def format_trip_output(trip):
    """Format a single trip for readable console output"""
    lines = []
    lines.append(f"  Passenger: {trip.get('passenger_name', 'N/A')}")
    lines.append(f"  Phone: {trip.get('passenger_phone', 'N/A')}")
    lines.append(f"  Pickup: {trip.get('source', 'N/A')}")

    if trip.get('pickup_latitude') and trip.get('pickup_longitude'):
        lines.append(f"    GPS: ({trip['pickup_latitude']}, {trip['pickup_longitude']})")

    lines.append(f"  Destination: {trip.get('destination', 'N/A')}")

    if trip.get('dropoff_latitude') and trip.get('dropoff_longitude'):
        lines.append(f"    GPS: ({trip['dropoff_latitude']}, {trip['dropoff_longitude']})")

    lines.append(f"  Pickup Time: {trip.get('pickup_date_time', 'N/A')}")
    lines.append(f"  Appointment: {trip.get('appointment_time', 'N/A')}")
    lines.append(f"  Service Type: {trip.get('service_type_id', 'N/A')}")
    lines.append(f"  Return Trip: {trip.get('return_trip_needed', 'N/A')}")

    return "\n".join(lines)


def main():
    """Main interactive flow"""

    print("=" * 80)
    print("NEMT TRIP PARSER - INTERACTIVE API TEST")
    print("=" * 80)
    print()
    print(f"API Endpoint: {API_URL}")
    print()

    # Step 1: Get file path
    while True:
        print("Step 1: Select Excel file")
        print("-" * 80)
        file_path = input("Enter path to Excel file (or drag & drop file here): ").strip()

        if not file_path:
            print("Error: Please provide a file path\n")
            continue

        # Validate file
        is_valid, error_msg = validate_file(file_path)

        if not is_valid:
            print(f"Error: {error_msg}\n")
            continue

        # Clean path for use
        file_path = file_path.strip('"').strip("'")
        print(f"✓ File validated: {Path(file_path).name}\n")
        break

    # Step 2: LLM enhancement option
    print("Step 2: LLM Enhancement")
    print("-" * 80)
    print("LLM enhancement uses Claude AI to clean and standardize addresses.")
    print("Example: 'Jackson 1611 12th' → 'Jackson Cancer Center, 1611 NW 12th Ave, Miami, FL'")
    use_llm = prompt_yes_no("Enable LLM enhancement?", default=False)
    print()

    # Step 3: Geocoding option
    print("Step 3: Geocoding")
    print("-" * 80)
    print("Geocoding converts addresses to GPS coordinates (latitude/longitude).")
    use_geocoding = prompt_yes_no("Enable geocoding?", default=True)
    print()

    # Summary
    print("=" * 80)
    print("PROCESSING")
    print("=" * 80)
    print(f"File: {Path(file_path).name}")
    print(f"LLM Enhancement: {'YES' if use_llm else 'NO'}")
    print(f"Geocoding: {'YES' if use_geocoding else 'NO'}")
    print()
    print("Uploading to API...")
    print()

    # Make API request
    try:
        headers = {'X-API-Key': API_KEY}

        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {
                'clinic_id': 'interactive_test',
                'use_llm': str(use_llm).lower(),
                'use_geocoding': str(use_geocoding).lower()
            }

            response = requests.post(
                API_URL,
                headers=headers,
                files=files,
                data=data,
                timeout=120
            )

        print("=" * 80)
        print(f"RESPONSE: {response.status_code}")
        print("=" * 80)
        print()

        if response.status_code == 200:
            result = response.json()

            if result.get('success'):
                print("✓ SUCCESS!")
                print()
                print(f"Total Trips: {result.get('total_trips', 0)}")
                print(f"Processing Time: {result.get('processing_time_seconds', 0):.2f}s")
                print()

                print("Features Used:")
                features = result.get('features_used', {})
                print(f"  - LLM Enhancement: {features.get('llm_enhancement', False)}")
                print(f"  - Geocoding: {features.get('geocoding', False)}")
                print()

                if result.get('trips') and len(result['trips']) > 0:
                    print("=" * 80)
                    print("FIRST TRIP (Sample):")
                    print("=" * 80)
                    print(format_trip_output(result['trips'][0]))
                    print()

                    if len(result['trips']) > 1:
                        print(f"... and {len(result['trips']) - 1} more trip(s)")
                        print()

                print("=" * 80)
                print("TEST COMPLETE!")
                print("=" * 80)
            else:
                print("✗ API returned success=false")
                print(f"Error: {result.get('error', 'Unknown error')}")
                sys.exit(1)

        else:
            print(f"✗ ERROR: HTTP {response.status_code}")
            print()
            print("Response:")
            print(response.text)
            sys.exit(1)

    except requests.Timeout:
        print("✗ ERROR: Request timed out (120 seconds)")
        print("The file may be too large or the server is slow.")
        sys.exit(1)

    except requests.RequestException as e:
        print(f"✗ ERROR: Network error")
        print(f"{e}")
        sys.exit(1)

    except FileNotFoundError:
        print(f"✗ ERROR: File not found: {file_path}")
        sys.exit(1)

    except Exception as e:
        print(f"✗ ERROR: Unexpected error")
        print(f"{e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
        sys.exit(0)
