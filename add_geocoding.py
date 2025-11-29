"""
Add geocoding to get latitude/longitude from addresses

Choose your geocoding provider below.
"""

import json
from typing import Optional, Tuple


# ============================================================================
# OPTION 1: Google Maps (Most Accurate, Requires API Key, Costs Money)
# ============================================================================

def geocode_google(address: str, api_key: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Geocode using Google Maps API

    Setup:
    1. Go to: https://console.cloud.google.com/
    2. Enable "Geocoding API"
    3. Create API key
    4. Install: pip install googlemaps

    Cost: $5 per 1,000 requests (first $200/month free)
    """
    try:
        import googlemaps

        gmaps = googlemaps.Client(key=api_key)
        result = gmaps.geocode(address)

        if result:
            location = result[0]['geometry']['location']
            return location['lat'], location['lng']
    except Exception as e:
        print(f"Geocoding error: {e}")

    return None, None


# ============================================================================
# OPTION 2: OpenStreetMap (Free, No API Key, Rate Limited)
# ============================================================================

def geocode_osm(address: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Geocode using OpenStreetMap (Nominatim)

    Setup:
    1. Install: pip install geopy

    Cost: FREE
    Limitations: 1 request per second max
    """
    try:
        from geopy.geocoders import Nominatim
        import time

        geolocator = Nominatim(user_agent="nemt_parser")

        # Respect rate limit (1 request per second)
        time.sleep(1)

        location = geolocator.geocode(address)

        if location:
            return location.latitude, location.longitude
    except Exception as e:
        print(f"Geocoding error: {e}")

    return None, None


# ============================================================================
# OPTION 3: Mapbox (Paid, Good Quality)
# ============================================================================

def geocode_mapbox(address: str, api_key: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Geocode using Mapbox

    Setup:
    1. Sign up at: https://www.mapbox.com/
    2. Get API token
    3. Install: pip install requests

    Cost: Free tier available, then paid
    """
    try:
        import requests

        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json"
        params = {
            'access_token': api_key,
            'limit': 1
        }

        response = requests.get(url, params=params)
        data = response.json()

        if data.get('features'):
            coords = data['features'][0]['geometry']['coordinates']
            # Mapbox returns [lon, lat] - we need [lat, lon]
            return coords[1], coords[0]
    except Exception as e:
        print(f"Geocoding error: {e}")

    return None, None


# ============================================================================
# Add Geocoding to Your Trips
# ============================================================================

def add_geocoding_to_json(
    input_file='messy_clinic_output.json',
    output_file='messy_clinic_with_coords.json',
    method='osm',  # 'google', 'osm', or 'mapbox'
    api_key=None
):
    """
    Add geocoding to existing JSON output

    Args:
        input_file: JSON file from parse_messy_clinic.py
        output_file: Where to save with coordinates
        method: 'google', 'osm', or 'mapbox'
        api_key: Required for google and mapbox
    """

    print("=" * 80)
    print("ADDING GEOCODING TO TRIPS")
    print("=" * 80)
    print(f"Method: {method.upper()}")
    print()

    # Load JSON
    with open(input_file, 'r') as f:
        trips = json.load(f)

    print(f"Loaded {len(trips)} trips")
    print()

    # Choose geocoding function
    if method == 'google':
        if not api_key:
            print("ERROR: Google Maps requires API key!")
            print("Get one here: https://console.cloud.google.com/")
            return
        geocode_func = lambda addr: geocode_google(addr, api_key)
    elif method == 'osm':
        geocode_func = geocode_osm
    elif method == 'mapbox':
        if not api_key:
            print("ERROR: Mapbox requires API key!")
            return
        geocode_func = lambda addr: geocode_mapbox(addr, api_key)
    else:
        print(f"ERROR: Unknown method '{method}'")
        return

    # Geocode each trip
    for i, trip in enumerate(trips, 1):
        print(f"Geocoding trip {i}/{len(trips)}: {trip['passenger_name']}")

        # Geocode pickup
        source = trip.get('source', '')
        if source:
            print(f"  Pickup: {source}")
            lat, lon = geocode_func(source)
            if lat and lon:
                trip['pickup_latitude'] = lat
                trip['pickup_longitude'] = lon
                print(f"    → {lat:.6f}, {lon:.6f}")
            else:
                print(f"    → Could not geocode")

        # Geocode destination
        destination = trip.get('destination', '')
        if destination:
            print(f"  Destination: {destination}")
            lat, lon = geocode_func(destination)
            if lat and lon:
                trip['dropoff_latitude'] = lat
                trip['dropoff_longitude'] = lon
                print(f"    → {lat:.6f}, {lon:.6f}")
            else:
                print(f"    → Could not geocode")

        print()

    # Save result
    with open(output_file, 'w') as f:
        json.dump(trips, f, indent=2)

    print("=" * 80)
    print(f"✓ Saved with coordinates to: {output_file}")
    print("=" * 80)


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    print()
    print("GEOCODING OPTIONS:")
    print("-" * 80)
    print()
    print("1. FREE (OpenStreetMap):")
    print("   - No API key needed")
    print("   - Slower (1 request/second)")
    print("   - Less accurate for messy addresses")
    print()
    print("2. PAID (Google Maps):")
    print("   - Requires API key")
    print("   - $5 per 1,000 requests (first $200/month free)")
    print("   - Very accurate")
    print()
    print("3. PAID (Mapbox):")
    print("   - Requires API token")
    print("   - Free tier available")
    print("   - Good accuracy")
    print()
    print("-" * 80)
    print()

    # Choose method
    choice = input("Which method? (1=OSM, 2=Google, 3=Mapbox): ").strip()

    if choice == '1':
        # Use OpenStreetMap (free)
        print("\nUsing OpenStreetMap (free)...")
        print("Installing geopy if needed...")
        import subprocess
        subprocess.run(['pip', 'install', 'geopy'], capture_output=True)

        add_geocoding_to_json(method='osm')

    elif choice == '2':
        # Use Google Maps
        api_key = input("\nEnter your Google Maps API key: ").strip()
        if api_key:
            print("\nInstalling googlemaps if needed...")
            import subprocess
            subprocess.run(['pip', 'install', 'googlemaps'], capture_output=True)

            add_geocoding_to_json(method='google', api_key=api_key)
        else:
            print("ERROR: API key required!")

    elif choice == '3':
        # Use Mapbox
        api_key = input("\nEnter your Mapbox API token: ").strip()
        if api_key:
            add_geocoding_to_json(method='mapbox', api_key=api_key)
        else:
            print("ERROR: API token required!")

    else:
        print("Invalid choice!")
