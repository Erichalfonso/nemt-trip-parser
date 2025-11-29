"""
Parse messy clinic data WITH LLM enhancement

Uses Claude/GPT to intelligently clean and enhance the data.
"""

import pandas as pd
from datetime import datetime
import json
import re
import os


# ============================================================================
# LLM INTEGRATION
# ============================================================================

def enhance_with_claude(trips_data):
    """
    Use Claude to enhance messy trip data

    Requires: pip install anthropic
    Set environment variable: ANTHROPIC_API_KEY
    """
    try:
        import anthropic
    except ImportError:
        print("ERROR: Install anthropic library first:")
        print("  pip install anthropic")
        return trips_data

    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("ERROR: Set ANTHROPIC_API_KEY environment variable")
        print("Get one at: https://console.anthropic.com/")
        return trips_data

    client = anthropic.Anthropic(api_key=api_key)

    print("\n" + "=" * 80)
    print("ENHANCING WITH CLAUDE AI")
    print("=" * 80)

    enhanced_trips = []

    for i, trip in enumerate(trips_data, 1):
        print(f"\nTrip {i}/{len(trips_data)}: {trip['passenger_name']}")

        # Build prompt for Claude
        prompt = f"""You are helping standardize NEMT (medical transportation) trip data.

Here's the messy trip data:
- Passenger: {trip['passenger_name']}
- Phone: {trip['passenger_phone']}
- Pickup address (messy): {trip['source']}
- Destination (messy): {trip['destination']}
- Notes: {trip['special_note']}

Miami/South Florida context is likely.

Please provide:
1. Cleaned, full pickup address (street, city, state, ZIP)
2. Full destination address (try to identify the actual clinic/hospital and provide full address)
3. Any improvements to the data

Return ONLY valid JSON in this format:
{{
  "pickup_full_address": "full street address, city, state ZIP",
  "destination_full_address": "full clinic address, city, state ZIP",
  "notes_cleaned": "any relevant notes"
}}"""

        try:
            # Call Claude
            message = client.messages.create(
                model="claude-3-haiku-20240307",  # Cheapest, fastest
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse response
            response_text = message.content[0].text

            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                enhanced_data = json.loads(json_match.group())

                # Update trip with enhanced data
                trip['source'] = enhanced_data.get('pickup_full_address', trip['source'])
                trip['destination'] = enhanced_data.get('destination_full_address', trip['destination'])

                if enhanced_data.get('notes_cleaned'):
                    trip['special_note'] = enhanced_data['notes_cleaned']

                print(f"  [OK] Enhanced:")
                print(f"    Pickup: {trip['source']}")
                print(f"    Destination: {trip['destination']}")

        except Exception as e:
            print(f"  [WARNING] LLM error: {e}")
            print(f"  Using original data")

        enhanced_trips.append(trip)

    return enhanced_trips


def enhance_with_openai(trips_data):
    """
    Use OpenAI GPT to enhance messy trip data

    Requires: pip install openai
    Set environment variable: OPENAI_API_KEY
    """
    try:
        from openai import OpenAI
    except ImportError:
        print("ERROR: Install openai library first:")
        print("  pip install openai")
        return trips_data

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("ERROR: Set OPENAI_API_KEY environment variable")
        return trips_data

    client = OpenAI(api_key=api_key)

    print("\n" + "=" * 80)
    print("ENHANCING WITH GPT AI")
    print("=" * 80)

    enhanced_trips = []

    for i, trip in enumerate(trips_data, 1):
        print(f"\nTrip {i}/{len(trips_data)}: {trip['passenger_name']}")

        prompt = f"""You are helping standardize NEMT trip data.

Messy data:
- Pickup: {trip['source']}
- Destination: {trip['destination']}
- Location: Miami/South Florida area

Provide cleaned addresses with full street, city, state, ZIP.
For destinations, identify the actual clinic/hospital name and full address.

Return ONLY JSON:
{{
  "pickup_full_address": "...",
  "destination_full_address": "..."
}}"""

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # Cheap and fast
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300
            )

            response_text = response.choices[0].message.content

            # Extract JSON
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                enhanced_data = json.loads(json_match.group())

                trip['source'] = enhanced_data.get('pickup_full_address', trip['source'])
                trip['destination'] = enhanced_data.get('destination_full_address', trip['destination'])

                print(f"  [OK] Enhanced")

        except Exception as e:
            print(f"  [WARNING] Error: {e}")

        enhanced_trips.append(trip)

    return enhanced_trips


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def parse_with_llm_enhancement(
    excel_file=r"C:\Users\erich\Downloads\ppol_example_small_clinic_messy.xlsx",
    llm_provider='claude'  # 'claude' or 'openai'
):
    """
    Parse messy Excel with LLM enhancement
    """

    print("=" * 80)
    print("PARSING WITH LLM ENHANCEMENT")
    print("=" * 80)
    print(f"Provider: {llm_provider.upper()}")
    print()

    # First, parse normally (reuse previous logic)
    from parse_messy_clinic import parse_messy_excel

    # Get basic parsed data
    print("Step 1: Basic parsing...")
    trips = parse_messy_excel()
    print(f"\n[OK] Parsed {len(trips)} trips")

    # Enhance with LLM
    print("\nStep 2: LLM enhancement...")

    if llm_provider == 'claude':
        enhanced_trips = enhance_with_claude(trips)
    elif llm_provider == 'openai':
        enhanced_trips = enhance_with_openai(trips)
    else:
        print(f"Unknown provider: {llm_provider}")
        return

    # Now geocode the enhanced addresses
    print("\nStep 3: Geocoding enhanced addresses...")

    try:
        from geopy.geocoders import Nominatim
        import time

        geolocator = Nominatim(user_agent="nemt_parser_llm")

        for trip in enhanced_trips:
            # Geocode pickup
            if trip['source']:
                time.sleep(1)
                try:
                    location = geolocator.geocode(trip['source'])
                    if location:
                        trip['pickup_latitude'] = location.latitude
                        trip['pickup_longitude'] = location.longitude
                        print(f"  [OK] Pickup geocoded: {location.latitude:.4f}, {location.longitude:.4f}")
                except:
                    pass

            # Geocode destination
            if trip['destination']:
                time.sleep(1)
                try:
                    location = geolocator.geocode(trip['destination'])
                    if location:
                        trip['dropoff_latitude'] = location.latitude
                        trip['dropoff_longitude'] = location.longitude
                        print(f"  [OK] Destination geocoded: {location.latitude:.4f}, {location.longitude:.4f}")
                except:
                    pass

    except ImportError:
        print("Install geopy for geocoding: pip install geopy")

    # Save result
    output_file = 'llm_enhanced_output.json'
    with open(output_file, 'w') as f:
        json.dump(enhanced_trips, f, indent=2)

    print("\n" + "=" * 80)
    print("FINAL OUTPUT:")
    print("=" * 80)
    print(json.dumps(enhanced_trips, indent=2))

    print("\n" + "=" * 80)
    print(f"[OK] Saved to: {output_file}")
    print("=" * 80)

    return enhanced_trips


# ============================================================================
# USAGE
# ============================================================================

if __name__ == "__main__":
    print()
    print("LLM-ENHANCED PARSING")
    print("-" * 80)
    print()
    print("This uses AI to:")
    print("  1. Clean messy addresses")
    print("  2. Infer full clinic addresses from names")
    print("  3. Standardize all data")
    print()
    print("Choose LLM provider:")
    print("  1. Claude (Anthropic) - Recommended")
    print("  2. OpenAI (GPT)")
    print()

    choice = input("Choice (1 or 2): ").strip()

    if choice == '1':
        print("\nUsing Claude!")
        print("\nSetup:")
        print("  1. Get API key: https://console.anthropic.com/")
        print("  2. Install: pip install anthropic")
        print("  3. Set: $env:ANTHROPIC_API_KEY='your-key-here'  (PowerShell)")
        print()

        api_key = input("Enter your Anthropic API key (or press Enter if already set): ").strip()
        if api_key:
            os.environ['ANTHROPIC_API_KEY'] = api_key

        parse_with_llm_enhancement(llm_provider='claude')

    elif choice == '2':
        print("\nUsing OpenAI!")
        print("\nSetup:")
        print("  1. Get API key: https://platform.openai.com/api-keys")
        print("  2. Install: pip install openai")
        print("  3. Set: $env:OPENAI_API_KEY='your-key-here'  (PowerShell)")
        print()

        api_key = input("Enter your OpenAI API key (or press Enter if already set): ").strip()
        if api_key:
            os.environ['OPENAI_API_KEY'] = api_key

        parse_with_llm_enhancement(llm_provider='openai')

    else:
        print("Invalid choice!")
