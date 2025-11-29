# Your Exact JSON Output Format ✅

## ✨ GOOD NEWS!

The parser now returns data in **YOUR EXACT JSON FORMAT**!

---

## 📊 Your Output Format

```json
{
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
```

---

## 🔄 How Excel Fields Map to Your Format

| Excel Column(s) | Your JSON Field | Notes |
|----------------|-----------------|-------|
| **Patient Name** | `passenger_name` | Direct mapping |
| **Patient Phone** | `passenger_phone` | Digits only (no dashes/spaces) |
| | `country_code` | Default: "+1" |
| | `passenger_language` | Default: "en" |
| **Wheelchair?** (Yes/No) | `service_type_id` | 1=ambulatory, 2=wheelchair, 3=stretcher |
| **Pick-up Address** + City + ZIP | `source` | Combined full address |
| | `pickup_latitude` | Requires geocoding* |
| | `pickup_longitude` | Requires geocoding* |
| **Drop-off Address** + City + ZIP | `destination` | Combined full address |
| | `dropoff_latitude` | Requires geocoding* |
| | `dropoff_longitude` | Requires geocoding* |
| **Appt Date** + **Appt Time** | `pickup_date_time` | Format: YYYY-MM-DD HH:MM:SS |
| | `appointment_time` | Format: YYYY-MM-DD HH:MM:SS |
| | `eta_time` | Optional (can calculate) |
| **Notes** | `special_note` | Special instructions |
| **Trip Type** | `return_trip_needed` | "yes" or "no" |
| | `return_trip_type` | "immediate" or "scheduled" |

\* *Geocoding (lat/lon) requires Google Maps API - see below*

---

## 🚀 Test It Now

```bash
cd C:\Users\erich\nemt-trip-parser
python test_your_format.py
```

This shows you EXACTLY what JSON you'll get!

---

## 🎯 Using the API

### Start the API

```bash
python -m nemt_parser.integrations.flask_adapter
```

### Upload Excel File

```bash
curl -X POST http://localhost:5000/api/nemt/upload \
  -F "file=@clinic_trips.xlsx" \
  -F "clinic_id=miami_medical"
```

### Response (Your Exact Format!)

```json
{
  "success": true,
  "trips_parsed": 15,
  "trips": [
    {
      "passenger_name": "John Smith",
      "country_code": "+1",
      "passenger_phone": "3051234567",
      "passenger_language": "en",
      "service_type_id": 2,
      "source": "123 Main St, Miami, FL 33101",
      "pickup_latitude": null,
      "pickup_longitude": null,
      "destination": "999 Hospital Blvd, Miami, FL 33125",
      "dropoff_latitude": null,
      "dropoff_longitude": null,
      "pickup_date_time": "2025-01-15 09:00:00",
      "eta_time": null,
      "appointment_time": "2025-01-15 09:00:00",
      "special_note": "Patient needs assistance walking",
      "return_trip_needed": "yes",
      "return_trip_type": "immediate"
    },
    // ... more trips
  ]
}
```

---

## 🌍 Adding Geocoding (Latitude/Longitude)

Currently, `pickup_latitude`, `pickup_longitude`, `dropoff_latitude`, and `dropoff_longitude` are `null` because geocoding requires an external service.

### Option 1: Google Maps Geocoding API (Recommended)

```python
# Install: pip install googlemaps

import googlemaps

def geocode_with_google(address: str):
    gmaps = googlemaps.Client(key='YOUR_API_KEY')
    result = gmaps.geocode(address)
    if result:
        location = result[0]['geometry']['location']
        return location['lat'], location['lng']
    return None, None
```

**Get API Key:** https://developers.google.com/maps/documentation/geocoding

**Cost:** $5 per 1000 requests (first $200/month free)

### Option 2: OpenStreetMap (Free)

```python
# Install: pip install geopy

from geopy.geocoders import Nominatim

def geocode_with_osm(address: str):
    geolocator = Nominatim(user_agent="nemt_parser")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    return None, None
```

**Limitations:** 1 request per second rate limit

### Enable Geocoding

Edit: `nemt_parser/core/output_schema.py`

Find the `geocode_address()` function and uncomment your preferred option!

---

## 📋 Field Details

### service_type_id

Determined from wheelchair/stretcher/ambulatory fields:

- `1` = Ambulatory (no wheelchair or stretcher)
- `2` = Wheelchair required
- `3` = Stretcher required

### return_trip_needed & return_trip_type

Determined from trip type:

| Excel Trip Type | return_trip_needed | return_trip_type |
|----------------|-------------------|------------------|
| "One Way" | "no" | null |
| "Round Trip" | "yes" | "immediate" |
| "Return" | "yes" | "scheduled" |

### phone

- Input: "(305) 123-4567" or "305-123-4567" or "3051234567"
- Output: "3051234567" (digits only)

### Addresses (source & destination)

Combines multiple Excel columns:

- Input: Address="123 Main St", City="Miami", State="FL", ZIP="33101"
- Output: "123 Main St, Miami, FL 33101"

---

## ✅ What's Working

- [x] Parse Excel from any clinic
- [x] Intelligent column mapping
- [x] Convert to YOUR exact JSON format
- [x] Handle phone number formatting
- [x] Determine service_type_id from wheelchair/stretcher
- [x] Combine addresses properly
- [x] Format datetimes correctly
- [x] Determine return trip fields

---

## ⚙️ What Requires Setup (Optional)

- [ ] Geocoding (lat/lon) - Requires Google Maps API or similar
- [ ] ETA calculation - Can add routing API
- [ ] Passenger language detection - Can add to column mapping

---

## 🎉 Summary

**YOU'RE DONE!**

The parser:
1. ✅ Receives Excel via API
2. ✅ Intelligently maps columns
3. ✅ Returns JSON in YOUR EXACT format
4. ✅ Ready to integrate with your website!

---

## 📞 Integration Example

```python
# Your website's upload handler
import requests

@app.route('/clinic-upload', methods=['POST'])
def upload():
    excel_file = request.files['file']
    clinic_id = request.form['clinic_id']

    # Send to parser
    response = requests.post('http://localhost:5000/api/nemt/upload',
        files={'file': excel_file},
        data={'clinic_id': clinic_id}
    )

    # Get trips in YOUR format
    data = response.json()

    if data['success']:
        trips = data['trips']  # Array of trips in your format!

        # Save to YOUR database or send to YOUR API
        for trip in trips:
            save_to_your_system(trip)

        return {"message": f"Uploaded {len(trips)} trips!"}
```

---

**No database on the parser side - just Excel in, JSON out!** 🚀
