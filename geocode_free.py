"""
FREE geocoding using OpenStreetMap (for testing)

Use this to test without Google API key.
For production, use Google Maps (more accurate).
"""

import json
import time


def geocode_trips_free(
    input_file='llm_enhanced_output.json',
    output_file='final_output_with_coords.json'
):
    """
    Add GPS coordinates using FREE OpenStreetMap

    Limitations:
    - 1 request per second (slower)
    - Less accurate than Google
    - Rate limited

    But it's FREE and works great for testing!
    """

    try:
        from geopy.geocoders import Nominatim
    except ImportError:
        print("Installing geopy...")
        import subprocess
        subprocess.run(['pip', 'install', 'geopy'], check=True)
        from geopy.geocoders import Nominatim

    print("=" * 80)
    print("FREE GEOCODING (OpenStreetMap)")
    print("=" * 80)
    print()
    print("Note: 1 request per second limit (will take ~6 seconds per trip)")
    print()

    # Initialize geocoder
    geolocator = Nominatim(user_agent="nemt_parser_production")

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
            time.sleep(1)  # Rate limit
            try:
                location = geolocator.geocode(pickup_address)
                if location:
                    trip['pickup_latitude'] = location.latitude
                    trip['pickup_longitude'] = location.longitude
                    print(f"    → {location.latitude:.6f}, {location.longitude:.6f}")
                    geocoded_count += 1
                else:
                    print(f"    → Not found")
                    failed_count += 1
            except Exception as e:
                print(f"    → Error: {e}")
                failed_count += 1

        # Geocode destination
        destination = trip.get('destination')
        if destination:
            print(f"  Destination: {destination}")
            time.sleep(1)  # Rate limit
            try:
                location = geolocator.geocode(destination)
                if location:
                    trip['dropoff_latitude'] = location.latitude
                    trip['dropoff_longitude'] = location.longitude
                    print(f"    → {location.latitude:.6f}, {location.longitude:.6f}")
                    geocoded_count += 1
                else:
                    print(f"    → Not found")
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
    print(f"Successfully geocoded: {geocoded_count}")
    print(f"Failed: {failed_count}")
    print()
    print(f"[OK] Saved to: {output_file}")
    print("=" * 80)

    # Show sample
    if trips:
        print()
        print("SAMPLE OUTPUT:")
        print("=" * 80)
        print(json.dumps(trips[0], indent=2))

    return trips


if __name__ == "__main__":
    print()
    print("FREE GEOCODING - GREAT FOR TESTING!")
    print()
    print("Pros:")
    print("  - FREE (no API key needed)")
    print("  - Works immediately")
    print()
    print("Cons:")
    print("  - Slower (1 request/second)")
    print("  - Less accurate for some addresses")
    print()
    print("For production, use Google Maps (geocode_with_google.py)")
    print()
    input("Press Enter to start geocoding...")
    print()

    geocode_trips_free()
