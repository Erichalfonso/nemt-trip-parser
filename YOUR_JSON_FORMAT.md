# JSON Output Format

Detailed field mapping from Excel input to standardized JSON output.

---

## Output Schema

Each trip object in the API response:

```json
{
  "passenger_name": "John Doe",
  "country_code": "+1",
  "passenger_phone": "1234567890",
  "passenger_language": "en",
  "service_type_id": 7,
  "source": "123 Main Street, Miami, FL 33125",
  "pickup_latitude": 25.7780,
  "pickup_longitude": -80.2154,
  "destination": "456 Elm Street, Miami, FL 33136",
  "dropoff_latitude": 25.7306,
  "dropoff_longitude": -73.9352,
  "pickup_date_time": "2025-11-27 15:30:00",
  "eta_time": null,
  "appointment_time": "2025-11-27 16:00:00",
  "special_note": "Please call when you arrive",
  "return_trip_needed": "yes",
  "return_trip_type": "immediate"
}
```

---

## Excel-to-JSON Field Mapping

| Excel Column(s) | JSON Field | Notes |
|-----------------|------------|-------|
| Patient Name | `passenger_name` | Direct mapping |
| Patient Phone | `passenger_phone` | Digits only, no formatting |
| | `country_code` | Default: "+1" |
| | `passenger_language` | Default: "en" |
| Wheelchair? (Yes/No) | `service_type_id` | 1=ambulatory, 7=wheelchair, 9=stretcher |
| Pick-up Address + City + ZIP | `source` | Combined full address |
| | `pickup_latitude` | Requires geocoding |
| | `pickup_longitude` | Requires geocoding |
| Drop-off Address + City + ZIP | `destination` | Combined full address |
| | `dropoff_latitude` | Requires geocoding |
| | `dropoff_longitude` | Requires geocoding |
| Appt Date + Appt Time | `pickup_date_time` | Format: YYYY-MM-DD HH:MM:SS |
| | `appointment_time` | Format: YYYY-MM-DD HH:MM:SS |
| | `eta_time` | Optional |
| Notes | `special_note` | Special instructions |
| Trip Type | `return_trip_needed` | "yes" or "no" |
| | `return_trip_type` | "immediate" or "scheduled" |

Geocoding (latitude/longitude) requires Google Maps API or OpenStreetMap. See configuration in [README.md](README.md).

---

## Using the API

### Upload

```bash
curl -X POST https://web-production-c09c8.up.railway.app/api/upload \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -F "file=@clinic_trips.xlsx" \
  -F "clinic_id=miami_medical"
```

### Response

```json
{
  "success": true,
  "total_trips": 15,
  "trips": [
    {
      "passenger_name": "John Smith",
      "country_code": "+1",
      "passenger_phone": "3051234567",
      "passenger_language": "en",
      "service_type_id": 7,
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
    }
  ]
}
```

---

## Field Details

### service_type_id

Determined from wheelchair/stretcher/ambulatory fields:

- `1` = Ambulatory (no wheelchair or stretcher)
- `7` = Wheelchair required
- `9` = Stretcher required

### return_trip_needed and return_trip_type

| Excel Trip Type | return_trip_needed | return_trip_type |
|----------------|-------------------|------------------|
| "One Way" | "no" | null |
| "Round Trip" | "yes" | "immediate" |
| "Return" | "yes" | "scheduled" |

### Phone numbers

- Input: "(305) 123-4567" or "305-123-4567" or "3051234567"
- Output: "3051234567" (digits only)

### Addresses (source and destination)

Multiple Excel columns are combined:

- Input: Address="123 Main St", City="Miami", State="FL", ZIP="33101"
- Output: "123 Main St, Miami, FL 33101"

---

## Geocoding

Coordinates are `null` unless geocoding is enabled.

**Google Maps (recommended):** Set `GOOGLE_MAPS_API_KEY` env var. Cost: $5 per 1,000 requests (first $200/month free).

**OpenStreetMap (free):** Set `GEOCODING_PROVIDER=osm`. Rate limit: 1 request/second.

Enable per-request with `use_geocoding=true` in the upload form data.

---

Back to [README](README.md).
