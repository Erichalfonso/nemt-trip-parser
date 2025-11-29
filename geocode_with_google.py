"""
Geocode addresses using Google Maps API

This adds lat/lon coordinates to your enhanced trip data.
"""

import json
import os


def geocode_trips_google(
    input_file='llm_enhanced_output.json',
    output_file='final_output_with_coords.json',
    api_key=None
):
    """
    Add GPS coordinates using Google Maps

    Args:
        input_file: JSON file with LLM-enhanced addresses
        output_file: Where to save with coordinates
        api_key: Your Google Maps API key
    """

    # Import Google Maps library
    try:
        import googlemaps
    except ImportError:
        print("ERROR: Install googlemaps first:")
        print("  pip install googlemaps")
        return

    # Get API key
    if not api_key:
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')

    if not api_key:
        print("ERROR: Google Maps API key required!")
        print()
        print("Get one at: https://console.cloud.google.com/")
        print()
        print("Then either:")
        print("  1. Pass as parameter: geocode_trips_google(api_key='your-key')")
        print("  2. Set environment: $env:GOOGLE_MAPS_API_KEY='your-key'")
        return

    print("=" * 80)
    print("GEOCODING WITH GOOGLE MAPS")
    print("=" * 80)
    print()

    # Initialize Google Maps client
    gmaps = googlemaps.Client(key=api_key)

    # Load trips
    with open(input_file, 'r') as f:
        trips = json.load(f)

    print(f"Loaded {len(trips)} trips")
    print()

    geocoded_count = 0
    failed_count = 0

    for i, trip in enumerate(trips, 1):
        print(f"Trip {i}/{len(trips)}: {trip['passenger_name']}")

        # Geocode pickup
        pickup_address = trip.get('source')
        if pickup_address:
            print(f"  Pickup: {pickup_address}")
            try:
                result = gmaps.geocode(pickup_address)
                if result:
                    location = result[0]['geometry']['location']
                    trip['pickup_latitude'] = location['lat']
                    trip['pickup_longitude'] = location['lng']
                    print(f"    → {location['lat']:.6f}, {location['lng']:.6f}")
                    geocoded_count += 1
                else:
                    print(f"    → No results found")
                    failed_count += 1
            except Exception as e:
                print(f"    → Error: {e}")
                failed_count += 1

        # Geocode destination
        destination = trip.get('destination')
        if destination:
            print(f"  Destination: {destination}")
            try:
                result = gmaps.geocode(destination)
                if result:
                    location = result[0]['geometry']['location']
                    trip['dropoff_latitude'] = location['lat']
                    trip['dropoff_longitude'] = location['lng']
                    print(f"    → {location['lat']:.6f}, {location['lng']:.6f}")
                    geocoded_count += 1
                else:
                    print(f"    → No results found")
                    failed_count += 1
            except Exception as e:
                print(f"    → Error: {e}")
                failed_count += 1

        print()

    # Save result
    with open(output_file, 'w') as f:
        json.dump(trips, f, indent=2)

    print("=" * 80)
    print("GEOCODING COMPLETE")
    print("=" * 80)
    print(f"Total addresses: {len(trips) * 2}")
    print(f"Successfully geocoded: {geocoded_count}")
    print(f"Failed: {failed_count}")
    print()
    print(f"[OK] Saved to: {output_file}")
    print("=" * 80)

    # Show sample
    if trips:
        print()
        print("SAMPLE OUTPUT (with coordinates):")
        print("=" * 80)
        print(json.dumps(trips[0], indent=2))

    return trips


def show_google_maps_setup():
    """Show instructions for getting Google Maps API key"""
    print()
    print("=" * 80)
    print("GOOGLE MAPS API SETUP")
    print("=" * 80)
    print()
    print("1. Go to: https://console.cloud.google.com/")
    print()
    print("2. Create a new project (or select existing)")
    print()
    print("3. Enable the Geocoding API:")
    print("   - Click 'APIs & Services' → 'Library'")
    print("   - Search for 'Geocoding API'")
    print("   - Click 'Enable'")
    print()
    print("4. Create credentials:")
    print("   - Go to 'APIs & Services' → 'Credentials'")
    print("   - Click 'Create Credentials' → 'API Key'")
    print("   - Copy the key")
    print()
    print("5. (Optional) Restrict the API key:")
    print("   - Click on the key")
    print("   - Under 'API restrictions', select 'Geocoding API'")
    print("   - Save")
    print()
    print("=" * 80)
    print()
    print("COST:")
    print("  - $5 per 1,000 requests")
    print("  - First $200/month FREE (40,000 requests)")
    print("  - Your estimated usage: ~12,000/month = $0 (within free tier)")
    print()
    print("=" * 80)
    print()


if __name__ == "__main__":
    import sys

    # Check if API key provided as argument
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        print(f"Using API key from command line")
        geocode_trips_google(api_key=api_key)
    else:
        # Show setup instructions
        show_google_maps_setup()

        print("Enter your Google Maps API key:")
        print("(or press Enter to use GOOGLE_MAPS_API_KEY environment variable)")
        print()

        api_key = input("API Key: ").strip()

        if api_key:
            # Use provided key
            geocode_trips_google(api_key=api_key)
        else:
            # Try environment variable
            geocode_trips_google()
