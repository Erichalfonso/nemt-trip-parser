"""
Geocode addresses using Google Maps API - OPTIMIZED with parallel processing

This adds lat/lon coordinates to your enhanced trip data.

OPTIMIZED: Uses ThreadPoolExecutor for parallel geocoding
- 1800 trips = 3600 addresses
- Sequential: ~3-6 minutes
- Parallel (10 workers): ~30-60 seconds
"""

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Optional


# Configuration
MAX_GEOCODE_WORKERS = 10  # Parallel geocoding requests


def geocode_single_address(gmaps, address: str) -> Tuple[Optional[float], Optional[float]]:
    """Geocode a single address, return (lat, lon) or (None, None)."""
    if not address:
        return None, None

    try:
        result = gmaps.geocode(address)
        if result:
            location = result[0]['geometry']['location']
            return location['lat'], location['lng']
        return None, None
    except Exception:
        return None, None


def geocode_trip(args: Tuple) -> Tuple[int, Dict]:
    """Geocode a single trip (both pickup and destination). Used for parallel execution."""
    idx, trip, gmaps = args

    # Geocode pickup
    pickup_address = trip.get('source')
    if pickup_address:
        lat, lng = geocode_single_address(gmaps, pickup_address)
        trip['pickup_latitude'] = lat
        trip['pickup_longitude'] = lng

    # Geocode destination
    destination = trip.get('destination')
    if destination:
        lat, lng = geocode_single_address(gmaps, destination)
        trip['dropoff_latitude'] = lat
        trip['dropoff_longitude'] = lng

    return idx, trip


def geocode_trips_google(
    input_file: str = 'llm_enhanced_output.json',
    output_file: str = 'final_output_with_coords.json',
    api_key: str = None,
    trips_list: List[Dict] = None,
    max_workers: int = MAX_GEOCODE_WORKERS
) -> List[Dict]:
    """
    Add GPS coordinates using Google Maps - PARALLEL PROCESSING

    Args:
        input_file: JSON file with LLM-enhanced addresses (ignored if trips_list provided)
        output_file: Where to save with coordinates
        api_key: Your Google Maps API key
        trips_list: Optional - pass trips directly instead of loading from file
        max_workers: Number of parallel geocoding threads (default 10)

    Returns:
        List of trips with coordinates added
    """

    # Import Google Maps library
    try:
        import googlemaps
    except ImportError:
        print("ERROR: Install googlemaps first:")
        print("  pip install googlemaps")
        return []

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
        return []

    print("=" * 80)
    print("GEOCODING WITH GOOGLE MAPS - PARALLEL PROCESSING")
    print("=" * 80)
    print()

    # Initialize Google Maps client
    gmaps = googlemaps.Client(key=api_key)

    # Load trips from file or use provided list
    if trips_list is not None:
        trips = trips_list
    else:
        with open(input_file, 'r') as f:
            trips = json.load(f)

    total_trips = len(trips)
    print(f"Loaded {total_trips} trips")
    print(f"Using {max_workers} parallel workers")
    print(f"Estimated addresses: {total_trips * 2}")
    print()
    print("Geocoding...")
    print("-" * 80)

    # Prepare arguments for parallel execution
    geocode_args = [(idx, trip.copy(), gmaps) for idx, trip in enumerate(trips)]

    # Process in parallel
    results = {}
    geocoded_count = 0
    failed_count = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {
            executor.submit(geocode_trip, args): args[0]
            for args in geocode_args
        }

        completed = 0
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                result_idx, geocoded_trip = future.result()
                results[result_idx] = geocoded_trip

                # Count successes/failures
                if geocoded_trip.get('pickup_latitude'):
                    geocoded_count += 1
                else:
                    failed_count += 1
                if geocoded_trip.get('dropoff_latitude'):
                    geocoded_count += 1
                else:
                    failed_count += 1

                completed += 1
                if completed % 50 == 0 or completed == total_trips:
                    print(f"  Progress: {completed}/{total_trips} trips geocoded")

            except Exception as e:
                print(f"  Trip {idx} failed: {e}")
                results[idx] = trips[idx]  # Keep original
                failed_count += 2
                completed += 1

    # Reconstruct trips in original order
    geocoded_trips = [results[i] for i in range(total_trips)]

    # Save result
    with open(output_file, 'w') as f:
        json.dump(geocoded_trips, f, indent=2)

    print()
    print("=" * 80)
    print("GEOCODING COMPLETE")
    print("=" * 80)
    print(f"Total addresses: {total_trips * 2}")
    print(f"Successfully geocoded: {geocoded_count}")
    print(f"Failed/missing: {failed_count}")
    print()
    print(f"[OK] Saved to: {output_file}")
    print("=" * 80)

    # Show sample
    if geocoded_trips:
        print()
        print("SAMPLE OUTPUT (with coordinates):")
        print("=" * 80)
        print(json.dumps(geocoded_trips[0], indent=2))

    return geocoded_trips


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
