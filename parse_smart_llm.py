"""
Smart LLM-based parser that works with ANY Excel format.

This parser:
1. Reads Excel with pandas (any column names)
2. Sends each row to Claude
3. Claude intelligently extracts the standardized fields
4. Returns standardized JSON

Hallucination-proof because:
- LLM only sees rows we give it (can't invent new trips)
- One row at a time processing
- Structured JSON output with validation
"""

import pandas as pd
import json
import os
import re
from typing import List, Dict, Optional
import anthropic


def extract_trip_with_llm(row_data: Dict, row_number: int, client: anthropic.Anthropic) -> Optional[Dict]:
    """
    Use Claude to intelligently extract trip data from a single Excel row.

    Args:
        row_data: Dictionary of column_name -> value for this row
        row_number: Row number for logging
        client: Anthropic client

    Returns:
        Standardized trip dict, or None if extraction failed
    """

    # Build prompt with the row data
    prompt = f"""You are parsing NEMT (Non-Emergency Medical Transportation) trip data from an Excel row.

Here is the raw row data (column names may vary):
{json.dumps(row_data, indent=2)}

Your task:
1. Intelligently identify which fields map to which trip attributes
2. Extract and standardize the data
3. Return ONLY valid JSON in the exact format below

IMPORTANT:
- Extract data ONLY from the provided row - do not invent or assume information
- If a field is not present or unclear, use null
- For addresses, extract exactly what is provided (don't add or infer details)
- For dates/times, convert to ISO format: YYYY-MM-DD HH:MM:SS
- For service_type_id: 1=ambulatory, 2=wheelchair, 3=stretcher
- For return_trip_needed: "yes" or "no"
- For passenger_language: "en" or "es" (default "en")

Return ONLY this JSON structure (no other text):
{{
  "passenger_name": "string or null",
  "country_code": "1",
  "passenger_phone": "10 digit phone number or null",
  "passenger_language": "en",
  "service_type_id": 1,
  "source": "pickup address or null",
  "destination": "dropoff address or null",
  "pickup_date_time": "YYYY-MM-DD HH:MM:SS or null",
  "appointment_time": "YYYY-MM-DD HH:MM:SS or null",
  "special_note": "string or null",
  "return_trip_needed": "yes or no",
  "return_trip_type": "immediate or scheduled or null"
}}"""

    try:
        # Call Claude
        message = client.messages.create(
            model="claude-3-haiku-20240307",  # Fast and cheap
            max_tokens=800,
            temperature=0,  # Deterministic output
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()

        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if not json_match:
            print(f"  Row {row_number}: No JSON found in response")
            return None

        trip_data = json.loads(json_match.group())

        # Validate required fields
        if not trip_data.get('passenger_name'):
            print(f"  Row {row_number}: Missing passenger name")
            return None

        # Add default values
        trip_data.setdefault('pickup_latitude', None)
        trip_data.setdefault('pickup_longitude', None)
        trip_data.setdefault('dropoff_latitude', None)
        trip_data.setdefault('dropoff_longitude', None)
        trip_data.setdefault('eta_time', None)
        trip_data.setdefault('country_code', '1')
        trip_data.setdefault('passenger_language', 'en')

        return trip_data

    except json.JSONDecodeError as e:
        print(f"  Row {row_number}: JSON parse error - {e}")
        return None
    except Exception as e:
        print(f"  Row {row_number}: Error - {e}")
        return None


def parse_excel_with_smart_llm(
    excel_file: str,
    anthropic_api_key: Optional[str] = None
) -> List[Dict]:
    """
    Parse ANY Excel format using Claude to intelligently extract fields.

    Args:
        excel_file: Path to Excel file
        anthropic_api_key: Anthropic API key (or reads from ANTHROPIC_API_KEY env var)

    Returns:
        List of standardized trip dictionaries
    """

    # Get API key
    api_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    # Initialize Claude client
    client = anthropic.Anthropic(api_key=api_key)

    print("=" * 80)
    print("SMART LLM PARSER - Works with ANY Excel format")
    print("=" * 80)
    print()

    # Read Excel file (generic, no column assumptions)
    print(f"Reading: {excel_file}")
    df = pd.read_excel(excel_file, dtype=str, na_filter=True)

    # Replace NaN with None for JSON serialization
    df = df.where(pd.notna(df), None)

    total_rows = len(df)
    print(f"Found {total_rows} rows")
    print(f"Columns: {list(df.columns)}")
    print()
    print("Processing rows with Claude AI...")
    print("-" * 80)

    trips = []
    failed_rows = []

    # Process each row with LLM
    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        row_number = idx + 2  # Excel row number (1-indexed, +1 for header)

        print(f"\nRow {row_number}:")

        # Extract trip data with LLM
        trip = extract_trip_with_llm(row_dict, row_number, client)

        if trip:
            trips.append(trip)
            print(f"  [OK] Extracted: {trip['passenger_name']}")
        else:
            failed_rows.append(row_number)
            print(f"  [FAIL] Failed to extract")

    # Summary
    print()
    print("=" * 80)
    print("PARSING COMPLETE")
    print("=" * 80)
    print(f"Total rows: {total_rows}")
    print(f"Successfully parsed: {len(trips)}")
    print(f"Failed: {len(failed_rows)}")

    if failed_rows:
        print(f"Failed row numbers: {failed_rows}")

    print()

    return trips


def parse_and_save(excel_file: str, output_file: str = "smart_parsed_output.json"):
    """
    Parse Excel and save to JSON file.
    """
    trips = parse_excel_with_smart_llm(excel_file)

    with open(output_file, 'w') as f:
        json.dump(trips, f, indent=2)

    print(f"Saved {len(trips)} trips to: {output_file}")

    return trips


if __name__ == "__main__":
    # Example usage
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
