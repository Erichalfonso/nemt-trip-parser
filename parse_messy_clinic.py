"""
Parse the messy clinic format AS-IS

Handles this clinic's exact format without asking them to change anything.
"""

import pandas as pd
from datetime import datetime, time as time_obj
import json
import re


def parse_messy_date(date_str):
    """Parse various date formats"""
    if not date_str or date_str.strip() == '':
        return None

    date_str = str(date_str).strip()

    # Try different formats
    formats = [
        "%d-%b",      # "5-Dec"
        "%m/%d/%y",   # "05/12/25"
        "%d-%m-%y",   # "12-05-25"
        "%m-%d-%Y",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            # If year is missing, use 2025
            if dt.year == 1900:
                dt = dt.replace(year=2025)
            return dt.date()
        except:
            continue

    return None


def parse_time_str(time_str):
    """Parse time strings like '9 am', '11:15a', '8:30'"""
    if not time_str or str(time_str).strip() == '':
        return None

    time_str = str(time_str).strip().lower()

    # Remove spaces
    time_str = time_str.replace(' ', '')

    # Try to parse
    try:
        # "9am"
        if 'am' in time_str or 'pm' in time_str:
            time_str = time_str.replace('a.m.', 'am').replace('p.m.', 'pm')
            for fmt in ['%I%p', '%I:%M%p']:
                try:
                    return datetime.strptime(time_str, fmt).time()
                except:
                    continue

        # "11:15"
        if ':' in time_str:
            parts = time_str.split(':')
            hour = int(parts[0])
            minute = int(parts[1][:2])  # Handle "11:15a"
            return time_obj(hour, minute)

        # Just number
        hour = int(time_str)
        return time_obj(hour, 0)
    except:
        pass

    return None


def clean_phone(phone):
    """Extract digits from phone number"""
    if not phone:
        return ""

    # Remove all non-digits
    digits = re.sub(r'\D', '', str(phone))
    return digits


def parse_address(address_str):
    """
    Parse messy address string.
    Try to extract what we can.
    """
    if not address_str:
        return "", "", "", ""

    address_str = str(address_str).strip()

    # Try to extract components
    # Look for city
    city = ""
    state = ""
    zip_code = ""
    street = address_str

    # Check for "miami fl" or "miami, fl"
    if "miami" in address_str.lower():
        city = "Miami"

    # Check for FL
    if " fl" in address_str.lower() or ",fl" in address_str.lower():
        state = "FL"

    # Try to extract ZIP (5 digits)
    zip_match = re.search(r'\b(\d{5})\b', address_str)
    if zip_match:
        zip_code = zip_match.group(1)

    # Street is everything (for now)
    street = address_str

    return street, city, state, zip_code


def determine_service_type(notes):
    """Determine service type from notes"""
    if not notes:
        return 1  # Default: ambulatory

    notes_lower = str(notes).lower()

    if 'wheelchair' in notes_lower or 'wc' in notes_lower:
        return 7
    elif 'stretcher' in notes_lower or 'gurney' in notes_lower:
        return 9
    else:
        return 1


def parse_return_trip(return_str):
    """Parse return trip field"""
    if not return_str:
        return "no", None

    return_lower = str(return_str).lower()

    if 'yes' in return_lower:
        # Check if immediate or scheduled
        if 'when done' in return_lower or 'call when' in return_lower:
            return "yes", "immediate"
        elif 'time unknown' in return_lower:
            return "yes", "scheduled"
        else:
            return "yes", "immediate"
    else:
        return "no", None


def parse_messy_excel(excel_file=None):
    """Parse the messy clinic Excel file"""

    if excel_file is None:
        import sys
        excel_file = sys.argv[1] if len(sys.argv) > 1 else "sample_data/clinic_a_trips.xlsx"

    print("=" * 80)
    print("PARSING MESSY CLINIC FORMAT")
    print("=" * 80)
    print()

    # Read Excel
    df = pd.read_excel(excel_file, dtype=str, na_filter=False)

    print(f"Found {len(df)} rows")
    print()

    # Parse each row
    trips = []

    for idx, row in df.iterrows():
        # Extract fields
        date_val = row.get('Date', '')
        name = row.get('Name', '').strip()
        phone = row.get('Phone', '')
        home_address = row.get('Address (Home)', '')
        clinic = row.get('Clinic / Doctor', '')
        appt_time_str = row.get('Appt time', '')
        pickup_time_str = row.get('Pickup time?', '')
        return_str = row.get('Return?', '')
        notes = row.get('Mobility / Notes', '')

        # Parse date
        appt_date = parse_messy_date(date_val)
        if not appt_date:
            print(f"[WARNING] Row {idx+1}: Could not parse date '{date_val}'")
            continue

        # Parse times
        appt_time = parse_time_str(appt_time_str)
        pickup_time = parse_time_str(pickup_time_str)

        # Parse address
        street, city, state, zip_code = parse_address(home_address)

        # Clean phone
        phone_clean = clean_phone(phone)

        # Determine service type
        service_type = determine_service_type(notes)

        # Parse return trip
        return_needed, return_type = parse_return_trip(return_str)

        # Build datetime strings
        if appt_time:
            appt_datetime = datetime.combine(appt_date, appt_time)
            appointment_time_str = appt_datetime.strftime("%Y-%m-%d %H:%M:%S")
        else:
            appointment_time_str = f"{appt_date} 00:00:00"

        if pickup_time:
            pickup_datetime = datetime.combine(appt_date, pickup_time)
            pickup_datetime_str = pickup_datetime.strftime("%Y-%m-%d %H:%M:%S")
        else:
            pickup_datetime_str = appointment_time_str

        # Build trip object in YOUR format
        trip = {
            "passenger_name": name,
            "country_code": "+1",
            "passenger_phone": phone_clean,
            "passenger_language": "es" if "spanish" in str(notes).lower() else "en",
            "service_type_id": service_type,

            # Source - use home address as-is
            "source": street if street else home_address,
            "pickup_latitude": None,  # Need geocoding
            "pickup_longitude": None,

            # Destination - use clinic name
            "destination": clinic,
            "dropoff_latitude": None,  # Need geocoding
            "dropoff_longitude": None,

            # Times
            "pickup_date_time": pickup_datetime_str,
            "eta_time": None,
            "appointment_time": appointment_time_str,

            # Notes
            "special_note": notes,

            # Return trip
            "return_trip_needed": return_needed,
            "return_trip_type": return_type
        }

        trips.append(trip)

        print(f"[OK] Parsed: {name}")

    print()
    print("=" * 80)
    print(f"SUCCESSFULLY PARSED {len(trips)} TRIPS")
    print("=" * 80)
    print()

    # Show sample
    if trips:
        print("SAMPLE TRIP (Your Format):")
        print("=" * 80)
        print(json.dumps(trips[0], indent=2))
        print()

    # Show all trips summary
    print("=" * 80)
    print("ALL TRIPS:")
    print("=" * 80)
    for i, trip in enumerate(trips, 1):
        print(f"\n{i}. {trip['passenger_name']}")
        print(f"   Phone: {trip['country_code']} {trip['passenger_phone']}")
        print(f"   Language: {trip['passenger_language']}")
        print(f"   From: {trip['source']}")
        print(f"   To: {trip['destination']}")
        print(f"   Pickup: {trip['pickup_date_time']}")
        print(f"   Appointment: {trip['appointment_time']}")
        print(f"   Service: {trip['service_type_id']} (1=ambulatory, 7=wheelchair, 9=stretcher)")
        print(f"   Return: {trip['return_trip_needed']} ({trip['return_trip_type']})")
        print(f"   Notes: {trip['special_note']}")

    # Full JSON output
    print()
    print("=" * 80)
    print("FULL JSON OUTPUT (Copy this!):")
    print("=" * 80)
    print(json.dumps(trips, indent=2))
    print()

    # Save to file
    with open('messy_clinic_output.json', 'w') as f:
        json.dump(trips, f, indent=2)

    print("=" * 80)
    print("[OK] JSON saved to: messy_clinic_output.json")
    print("=" * 80)

    return trips


if __name__ == "__main__":
    parse_messy_excel()
