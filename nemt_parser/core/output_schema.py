"""
Output schema matching your exact API requirements.

This transforms the parsed trip data into the exact JSON format you need.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, computed_field


class TripOutput(BaseModel):
    """
    Your exact output format for trips.

    This is what gets returned in the JSON response.
    """

    # Passenger Information
    passenger_name: str = Field(..., description="Passenger full name")
    country_code: str = Field(default="+1", description="Phone country code")
    passenger_phone: str = Field(..., description="Passenger phone number (digits only)")
    passenger_language: str = Field(default="en", description="Passenger language code")

    # Service Type
    service_type_id: int = Field(..., description="Service type ID (1=ambulatory, 7=wheelchair, 9=stretcher)")

    # Pickup Location
    source: str = Field(..., description="Full pickup address")
    pickup_latitude: Optional[float] = Field(None, description="Pickup GPS latitude")
    pickup_longitude: Optional[float] = Field(None, description="Pickup GPS longitude")

    # Dropoff Location
    destination: str = Field(..., description="Full dropoff address")
    dropoff_latitude: Optional[float] = Field(None, description="Dropoff GPS latitude")
    dropoff_longitude: Optional[float] = Field(None, description="Dropoff GPS longitude")

    # Time Information
    pickup_date_time: str = Field(..., description="Pickup datetime in format: YYYY-MM-DD HH:MM:SS")
    eta_time: Optional[str] = Field(None, description="Estimated travel time (e.g., '15 mins')")
    appointment_time: str = Field(..., description="Appointment datetime in format: YYYY-MM-DD HH:MM:SS")

    # Additional Details
    special_note: Optional[str] = Field(None, description="Special instructions")

    # Return Trip
    return_trip_needed: str = Field(default="no", description="'yes' or 'no'")
    return_trip_type: Optional[str] = Field(None, description="'immediate' or 'scheduled'")

    class Config:
        json_schema_extra = {
            "example": {
                "passenger_name": "John Doe",
                "country_code": "+1",
                "passenger_phone": "1234567890",
                "passenger_language": "en",
                "service_type_id": 2,
                "source": "123 Main Street, City A",
                "pickup_latitude": 40.712776,
                "pickup_longitude": -74.005974,
                "destination": "456 Elm Street, City B",
                "dropoff_latitude": 40.730610,
                "dropoff_longitude": -73.935242,
                "pickup_date_time": "2025-11-27 15:30:00",
                "eta_time": "15 mins",
                "appointment_time": "2025-11-27 16:00:00",
                "special_note": "Please call when you arrive",
                "return_trip_needed": "yes",
                "return_trip_type": "immediate"
            }
        }


def convert_to_output_format(trip) -> TripOutput:
    """
    Convert parsed trip to your exact output format.

    Args:
        trip: Parsed Trip object from Excel

    Returns:
        TripOutput in your exact JSON format
    """
    from datetime import datetime, time

    # Combine address components into full address
    source_address = f"{trip.pickup_address}, {trip.pickup_city}, {trip.pickup_state} {trip.pickup_zip}"
    destination_address = f"{trip.dropoff_address}, {trip.dropoff_city}, {trip.dropoff_state} {trip.dropoff_zip}"

    # Clean phone number to digits only
    phone_digits = ""
    if trip.patient_phone:
        phone_digits = ''.join(filter(str.isdigit, trip.patient_phone))

    # Determine service_type_id from wheelchair/stretcher/ambulatory
    if trip.stretcher:
        service_type_id = 9  # Stretcher
    elif trip.wheelchair:
        service_type_id = 7  # Wheelchair
    else:
        service_type_id = 1  # Ambulatory

    # Format datetimes
    # Assume pickup is 30 mins before appointment
    appointment_dt = datetime.combine(trip.appointment_date, trip.appointment_time or time(0, 0))
    pickup_dt = appointment_dt  # Or calculate based on your logic

    pickup_date_time = pickup_dt.strftime("%Y-%m-%d %H:%M:%S")
    appointment_time = appointment_dt.strftime("%Y-%m-%d %H:%M:%S")

    # Determine return trip
    return_trip_needed = "yes" if trip.trip_type.value in ["round_trip", "return"] else "no"
    return_trip_type = "immediate" if trip.trip_type.value == "round_trip" else None

    return TripOutput(
        passenger_name=trip.patient_name,
        country_code="+1",  # Default, can be configurable
        passenger_phone=phone_digits,
        passenger_language="en",  # Default, can be added to Excel mapping
        service_type_id=service_type_id,
        source=source_address,
        pickup_latitude=None,  # Requires geocoding (see below)
        pickup_longitude=None,  # Requires geocoding (see below)
        destination=destination_address,
        dropoff_latitude=None,  # Requires geocoding (see below)
        dropoff_longitude=None,  # Requires geocoding (see below)
        pickup_date_time=pickup_date_time,
        eta_time=None,  # Can calculate or leave None
        appointment_time=appointment_time,
        special_note=trip.notes,
        return_trip_needed=return_trip_needed,
        return_trip_type=return_trip_type
    )


# ============================================================================
# OPTIONAL: Geocoding Integration
# ============================================================================

def geocode_address(address: str) -> tuple[Optional[float], Optional[float]]:
    """
    Convert address to latitude/longitude.

    You'll need to integrate with a geocoding service:
    - Google Maps Geocoding API (paid, most accurate)
    - OpenStreetMap Nominatim (free, rate limited)
    - Mapbox (paid)
    - HERE Maps (paid)

    This is a placeholder - you need to add your API key and service.
    """
    # OPTION 1: Google Maps (requires API key)
    # import googlemaps
    # gmaps = googlemaps.Client(key='YOUR_API_KEY')
    # result = gmaps.geocode(address)
    # if result:
    #     location = result[0]['geometry']['location']
    #     return location['lat'], location['lng']

    # OPTION 2: OpenStreetMap (free, but rate limited)
    # from geopy.geocoders import Nominatim
    # geolocator = Nominatim(user_agent="nemt_parser")
    # location = geolocator.geocode(address)
    # if location:
    #     return location.latitude, location.longitude

    # For now, return None (no geocoding)
    return None, None


def convert_with_geocoding(trip) -> TripOutput:
    """
    Convert trip with geocoding enabled.

    NOTE: Geocoding requires external API and may have costs!
    """
    output = convert_to_output_format(trip)

    # Geocode pickup address
    pickup_lat, pickup_lon = geocode_address(output.source)
    output.pickup_latitude = pickup_lat
    output.pickup_longitude = pickup_lon

    # Geocode dropoff address
    dropoff_lat, dropoff_lon = geocode_address(output.destination)
    output.dropoff_latitude = dropoff_lat
    output.dropoff_longitude = dropoff_lon

    return output
