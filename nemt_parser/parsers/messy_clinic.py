"""
Parse messy clinic Excel formats AS-IS.

Handles various clinic formats without asking them to change anything.
Detects column names automatically using pattern matching.
"""

import pandas as pd
from datetime import datetime, time as time_obj
import json
import re


# Patterns for detecting which column maps to which field.
# Each field has a list of regex patterns (matched case-insensitively).
COLUMN_PATTERNS = {
    "name": [
        r"patient.*name", r"full.*name", r"passenger.*name", r"client.*name",
        r"^name$", r"^patient$",
    ],
    "phone": [
        r"phone", r"telephone", r"contact.*number", r"cell", r"mobile",
    ],
    "medicaid_id": [
        r"medicaid", r"insurance.*id", r"member.*id", r"policy.*number",
    ],
    "date": [
        r"appt.*date", r"appointment.*date", r"service.*date", r"trip.*date",
        r"visit.*date", r"^date$",
    ],
    "time": [
        r"appt.*time", r"appointment.*time", r"service.*time", r"visit.*time",
        r"pickup.*time", r"scheduled.*time", r"^time$",
    ],
    "pickup_address": [
        r"pick.?up.*address", r"pick.?up.*location", r"origin.*address",
        r"from.*address", r"source.*address", r"address.*home",
        r"home.*address", r"pickup.*location",
    ],
    "pickup_city": [
        r"pick.?up.*city", r"origin.*city", r"from.*city",
    ],
    "pickup_zip": [
        r"pick.?up.*zip", r"origin.*zip", r"from.*zip",
    ],
    "dropoff_address": [
        r"drop.?off.*address", r"drop.?off.*location", r"destination.*address",
        r"to.*address", r"clinic.*doctor", r"dropoff.*location",
        r"destination$",
    ],
    "dropoff_city": [
        r"drop.?off.*city", r"destination.*city", r"to.*city",
    ],
    "dropoff_zip": [
        r"drop.?off.*zip", r"destination.*zip", r"to.*zip",
    ],
    "wheelchair": [
        r"wheelchair", r"^wc", r"wc.*required", r"mobility.*aid",
    ],
    "notes": [
        r"notes", r"comments", r"special.*instruction", r"remarks",
        r"mobility.*notes",
    ],
    "return_trip": [
        r"return",
    ],
    "pickup_time": [
        r"pickup.*time\??$",
    ],
}


def detect_columns(df_columns):
    """
    Detect which DataFrame column maps to which standardized field.

    Returns a dict like {"name": "Patient Name", "date": "Appt Date", ...}
    """
    columns_lower = {col: col.lower().strip() for col in df_columns}
    mapping = {}

    for field, patterns in COLUMN_PATTERNS.items():
        for col, col_lower in columns_lower.items():
            if col in mapping.values():
                continue
            for pattern in patterns:
                if re.search(pattern, col_lower):
                    mapping[field] = col
                    break
            if field in mapping:
                break

    return mapping


def parse_messy_date(date_str):
    """Parse various date formats"""
    if not date_str or str(date_str).strip() == '':
        return None

    date_str = str(date_str).strip()

    # Try different formats
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%d-%b",      # "5-Dec"
        "%d-%m-%y",   # "12-05-25"
        "%m-%d-%Y",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y %H:%M",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            # If year is missing, use 2025
            if dt.year == 1900:
                dt = dt.replace(year=2025)
            return dt.date()
        except (ValueError, TypeError):
            continue

    # Try pandas as fallback
    try:
        dt = pd.to_datetime(date_str)
        return dt.date()
    except (ValueError, TypeError):
        pass

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
    """
    Parse a messy clinic Excel file.

    Automatically detects column names using pattern matching,
    so it works with various clinic formats without configuration.
    """

    if excel_file is None:
        import sys
        excel_file = sys.argv[1] if len(sys.argv) > 1 else "sample_data/clinic_a_trips.xlsx"

    # Read Excel
    df = pd.read_excel(excel_file, dtype=str, na_filter=False)

    # Detect column mapping
    col_map = detect_columns(df.columns)

    # Helper to get a value from a row using the detected mapping
    def get_val(row, field):
        col = col_map.get(field)
        if col and col in row:
            val = row[col]
            return str(val).strip() if val else ''
        return ''

    # Parse each row
    trips = []

    for idx, row in df.iterrows():
        # Extract fields using detected columns
        name = get_val(row, 'name')
        if not name:
            continue  # Skip rows without a name

        date_val = get_val(row, 'date')
        phone = get_val(row, 'phone')
        pickup_addr = get_val(row, 'pickup_address')
        pickup_city = get_val(row, 'pickup_city')
        pickup_zip = get_val(row, 'pickup_zip')
        dropoff_addr = get_val(row, 'dropoff_address')
        dropoff_city = get_val(row, 'dropoff_city')
        dropoff_zip = get_val(row, 'dropoff_zip')
        appt_time_str = get_val(row, 'time')
        pickup_time_str = get_val(row, 'pickup_time')
        return_str = get_val(row, 'return_trip')
        wheelchair_str = get_val(row, 'wheelchair')
        notes = get_val(row, 'notes')

        # Parse date
        appt_date = parse_messy_date(date_val)
        if not appt_date:
            continue

        # Parse times
        appt_time = parse_time_str(appt_time_str)
        pickup_time = parse_time_str(pickup_time_str)

        # Build source address: use separate fields if available, else use combined
        if pickup_city or pickup_zip:
            source = ', '.join(filter(None, [pickup_addr, pickup_city, 'FL', pickup_zip]))
        else:
            # Combined address field (like clinic_c: "700 Bay St, Tampa, FL 33601")
            source = pickup_addr

        # Build destination address
        if dropoff_city or dropoff_zip:
            destination = ', '.join(filter(None, [dropoff_addr, dropoff_city, 'FL', dropoff_zip]))
        else:
            destination = dropoff_addr

        # Clean phone
        phone_clean = clean_phone(phone)

        # Determine service type from wheelchair column or notes
        service_type = determine_service_type(wheelchair_str or notes)

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

        # Build trip object
        trip = {
            "passenger_name": name,
            "country_code": "+1",
            "passenger_phone": phone_clean,
            "passenger_language": "es" if "spanish" in str(notes).lower() else "en",
            "service_type_id": service_type,
            "source": source,
            "pickup_latitude": None,
            "pickup_longitude": None,
            "destination": destination,
            "dropoff_latitude": None,
            "dropoff_longitude": None,
            "pickup_date_time": pickup_datetime_str,
            "eta_time": None,
            "appointment_time": appointment_time_str,
            "special_note": notes if notes else None,
            "return_trip_needed": return_needed,
            "return_trip_type": return_type,
        }

        trips.append(trip)

    return trips


if __name__ == "__main__":
    parse_messy_excel()
