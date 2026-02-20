"""
Smart LLM-based parser that works with ANY Excel format.

OPTIMIZED APPROACH:
1. LLM analyzes column headers + sample rows ONCE
2. LLM outputs a column mapping (which column = which field)
3. Python/pandas applies that mapping to ALL rows instantly

Result: 1 LLM call + fast pandas = ~10 seconds for ANY file size
(vs. old approach: 1 LLM call per row = 30-60 minutes for 1800 rows)
"""

import pandas as pd
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional
import anthropic


def get_column_mapping_from_llm(columns: List[str], sample_rows: List[Dict], client: anthropic.Anthropic) -> Dict:
    """
    Use Claude to analyze column headers and sample data, then output a mapping.

    This is called ONCE per file, not per row.

    Returns a dict like:
    {
        "passenger_name": "Patient Name",
        "passenger_phone": "Phone",
        "source": "Pickup Address",
        ...
    }
    """

    prompt = f"""You are analyzing an Excel file containing NEMT (Non-Emergency Medical Transportation) trip data.

COLUMN HEADERS:
{json.dumps(columns, indent=2)}

SAMPLE ROWS (first 5 rows of data):
{json.dumps(sample_rows, indent=2)}

Your task: Figure out which Excel column maps to which standardized field.

STANDARDIZED FIELDS WE NEED:
- passenger_name: Patient/passenger full name
- passenger_phone: Phone number
- source: Pickup address (home address, origin)
- destination: Dropoff address (clinic, doctor, hospital)
- date: Trip date (might be combined with time)
- appointment_time: Appointment time at destination
- pickup_time: Pickup time (might not exist)
- service_type: Ambulatory/wheelchair/stretcher (might be in notes)
- return_trip: Whether return trip is needed
- notes: Special notes, mobility info, etc.
- language: Patient language preference (might not exist)

RULES:
1. Look at BOTH column names AND sample data to determine mappings
2. If a field doesn't exist in the data, map it to null
3. Some columns might contain combined data (e.g., "Name & Phone" has both)
4. Date and time might be in same column or separate columns
5. Address might be split across columns or in one column

Return ONLY this JSON (no other text):
{{
    "passenger_name": "exact column name or null",
    "passenger_phone": "exact column name or null",
    "source": "exact column name or null",
    "destination": "exact column name or null",
    "date": "exact column name or null",
    "appointment_time": "exact column name or null",
    "pickup_time": "exact column name or null",
    "service_type": "exact column name or null",
    "return_trip": "exact column name or null",
    "notes": "exact column name or null",
    "language": "exact column name or null"
}}"""

    try:
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()

        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if not json_match:
            print("WARNING: Could not parse LLM mapping response")
            return {}

        mapping = json.loads(json_match.group())
        return mapping

    except Exception as e:
        print(f"ERROR getting column mapping: {e}")
        return {}


def parse_date_value(value) -> Optional[str]:
    """Parse various date formats into YYYY-MM-DD"""
    if not value or pd.isna(value):
        return None

    value = str(value).strip()
    if not value:
        return None

    # Try various formats
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%d/%m/%Y",
        "%d-%b-%Y",
        "%d-%b",
        "%m-%d-%Y",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y %H:%M",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(value, fmt)
            if dt.year < 100:
                dt = dt.replace(year=dt.year + 2000)
            elif dt.year == 1900:
                dt = dt.replace(year=2025)
            return dt.strftime("%Y-%m-%d")
        except:
            continue

    # Try pandas
    try:
        dt = pd.to_datetime(value)
        return dt.strftime("%Y-%m-%d")
    except:
        pass

    return None


def parse_time_value(value) -> Optional[str]:
    """Parse various time formats into HH:MM:SS"""
    if not value or pd.isna(value):
        return None

    value = str(value).strip().lower()
    if not value:
        return None

    # Clean up
    value = value.replace(' ', '').replace('a.m.', 'am').replace('p.m.', 'pm')

    # Try various formats
    formats = [
        "%H:%M:%S",
        "%H:%M",
        "%I:%M%p",
        "%I:%M %p",
        "%I%p",
        "%I %p",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%H:%M:%S")
        except:
            continue

    # Try just a number (hour)
    try:
        hour = int(re.search(r'\d+', value).group())
        if hour < 24:
            return f"{hour:02d}:00:00"
    except:
        pass

    return None


def clean_phone(value) -> Optional[str]:
    """Extract digits from phone number"""
    if not value or pd.isna(value):
        return None

    digits = re.sub(r'\D', '', str(value))
    if len(digits) >= 10:
        return digits[-10:]  # Last 10 digits
    return digits if digits else None


def determine_service_type(value) -> int:
    """Determine service type: 1=ambulatory, 7=wheelchair, 9=stretcher"""
    if not value or pd.isna(value):
        return 1

    value_lower = str(value).lower()

    if any(w in value_lower for w in ['wheelchair', 'wc', 'w/c']):
        return 7
    elif any(w in value_lower for w in ['stretcher', 'gurney', 'strech']):
        return 9
    else:
        return 1


def parse_return_trip(value) -> tuple:
    """Parse return trip field, returns (needed: str, type: str)"""
    if not value or pd.isna(value):
        return "no", None

    value_lower = str(value).lower()

    if any(w in value_lower for w in ['yes', 'y', 'true', '1', 'return']):
        if any(w in value_lower for w in ['when done', 'call when', 'immediate', 'wait']):
            return "yes", "immediate"
        else:
            return "yes", "scheduled"

    return "no", None


def apply_mapping_to_dataframe(df: pd.DataFrame, mapping: Dict) -> List[Dict]:
    """
    Apply the LLM-generated mapping to extract trips from the dataframe.
    This is the fast part - pure pandas, no LLM calls.
    """

    trips = []

    for idx, row in df.iterrows():
        # Get raw values using the mapping
        def get_val(field):
            col = mapping.get(field)
            if col and col != "null" and col in row:
                val = row[col]
                if pd.isna(val):
                    return None
                return str(val).strip() if val else None
            return None

        # Extract and clean fields
        name = get_val('passenger_name')
        if not name:
            continue  # Skip rows without a name

        phone = clean_phone(get_val('passenger_phone'))
        source = get_val('source')
        destination = get_val('destination')

        # Parse date and times
        date_str = parse_date_value(get_val('date'))
        appt_time = parse_time_value(get_val('appointment_time'))
        pickup_time = parse_time_value(get_val('pickup_time'))

        # Combine date and time
        if date_str:
            if appt_time:
                appointment_datetime = f"{date_str} {appt_time}"
            else:
                appointment_datetime = f"{date_str} 00:00:00"

            if pickup_time:
                pickup_datetime = f"{date_str} {pickup_time}"
            else:
                pickup_datetime = appointment_datetime
        else:
            appointment_datetime = None
            pickup_datetime = None

        # Service type from notes or dedicated column
        notes = get_val('notes')
        service_type_raw = get_val('service_type')
        service_type = determine_service_type(service_type_raw or notes)

        # Return trip
        return_raw = get_val('return_trip')
        return_needed, return_type = parse_return_trip(return_raw)

        # Language detection
        language_raw = get_val('language')
        if language_raw:
            lang_lower = language_raw.lower()
            # Check for Spanish indicators
            if any(x in lang_lower for x in ['spanish', 'espanol', 'español', 'es', 'spa']):
                language = 'es'
            else:
                language = 'en'
        else:
            language = 'en'

        # Build trip object
        trip = {
            "passenger_name": name,
            "country_code": "1",
            "passenger_phone": phone,
            "passenger_language": language,
            "service_type_id": service_type,
            "source": source,
            "pickup_latitude": None,
            "pickup_longitude": None,
            "destination": destination,
            "dropoff_latitude": None,
            "dropoff_longitude": None,
            "pickup_date_time": pickup_datetime,
            "eta_time": None,
            "appointment_time": appointment_datetime,
            "special_note": notes,
            "return_trip_needed": return_needed,
            "return_trip_type": return_type
        }

        trips.append(trip)

    return trips


def parse_excel_with_smart_llm(
    excel_file: str,
    anthropic_api_key: Optional[str] = None
) -> List[Dict]:
    """
    Parse ANY Excel format using smart schema detection.

    OPTIMIZED APPROACH:
    1. LLM analyzes headers + sample rows (1 API call)
    2. Python applies mapping to all rows (instant)

    For 1800 rows: ~10 seconds total (vs. 30-60 minutes with old approach)
    """

    # Get API key
    api_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    client = anthropic.Anthropic(api_key=api_key)

    print("=" * 80)
    print("SMART LLM PARSER - SCHEMA DETECTION MODE")
    print("=" * 80)
    print()

    # Read Excel file
    print(f"Reading: {excel_file}")
    df = pd.read_excel(excel_file, dtype=str, na_filter=True)

    total_rows = len(df)
    columns = list(df.columns)

    print(f"Found {total_rows} rows")
    print(f"Columns: {columns}")
    print()

    # Get sample rows for LLM analysis
    sample_rows = df.head(5).to_dict('records')

    print("Step 1: Analyzing schema with LLM (1 API call)...")
    print("-" * 80)

    # Get column mapping from LLM
    mapping = get_column_mapping_from_llm(columns, sample_rows, client)

    if not mapping:
        print("ERROR: Could not determine column mapping")
        return []

    print("Column mapping detected:")
    for field, col in mapping.items():
        if col and col != "null":
            print(f"  {field} <- '{col}'")
    print()

    print(f"Step 2: Applying mapping to all {total_rows} rows...")
    print("-" * 80)

    # Apply mapping to all rows (fast!)
    trips = apply_mapping_to_dataframe(df, mapping)

    print()
    print("=" * 80)
    print("PARSING COMPLETE")
    print("=" * 80)
    print(f"Total rows: {total_rows}")
    print(f"LLM API calls: 1")
    print(f"Successfully parsed: {len(trips)} trips")
    print(f"Failed/skipped: {total_rows - len(trips)}")
    print()

    return trips


def parse_and_save(excel_file: str, output_file: str = "smart_parsed_output.json"):
    """Parse Excel and save to JSON file."""
    trips = parse_excel_with_smart_llm(excel_file)

    with open(output_file, 'w') as f:
        json.dump(trips, f, indent=2)

    print(f"Saved {len(trips)} trips to: {output_file}")
    return trips


if __name__ == "__main__":
    excel_file = r"C:\Users\erich\Downloads\ppol_example_small_clinic_messy.xlsx"

    if os.path.exists(excel_file):
        trips = parse_and_save(excel_file)

        if trips:
            print("\n" + "=" * 80)
            print("FIRST TRIP SAMPLE:")
            print("=" * 80)
            print(json.dumps(trips[0], indent=2))
    else:
        print(f"File not found: {excel_file}")
        print("\nUsage:")
        print("  from parse_smart_llm import parse_excel_with_smart_llm")
        print("  trips = parse_excel_with_smart_llm('your_file.xlsx')")
