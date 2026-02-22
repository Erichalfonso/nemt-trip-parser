# API Documentation

Complete reference for the NEMT Trip Parser API. For integration examples, see [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md).

## Base URL

**Production:** `https://web-production-c09c8.up.railway.app`

**Local development:** `http://localhost:5001`

## Authentication

All endpoints except `/health` require an API key passed via the `X-API-Key` header:

```
X-API-Key: YOUR_API_KEY_HERE
```

The API key is set via the `API_KEY` environment variable on the server.

---

## Endpoints

### GET /health

Health check endpoint. No authentication required.

**Response (200):**

```json
{
  "status": "ok",
  "timestamp": "2025-11-29T12:00:00.000000",
  "version": "1.0.0",
  "features": {
    "llm_enhancement": true,
    "google_geocoding": true,
    "free_geocoding": true
  }
}
```

---

### POST /api/upload

Upload an Excel file and receive standardized trip JSON.

**Headers:**

| Header | Required | Description |
|--------|----------|-------------|
| `X-API-Key` | Yes | API authentication key |

**Request body:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | Excel file (.xlsx or .xls), max 16 MB |
| `clinic_id` | string | No | Clinic identifier for tracking (default: "unknown") |
| `use_llm` | string | No | Enable LLM parsing: "true" or "false" |
| `use_geocoding` | string | No | Enable geocoding: "true" or "false" |

**Example request:**

```bash
curl -X POST https://web-production-c09c8.up.railway.app/api/upload \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -F "file=@clinic_trips.xlsx" \
  -F "clinic_id=clinic_123" \
  -F "use_geocoding=true" \
  -F "use_llm=true"
```

**Success response (200):**

```json
{
  "success": true,
  "trips": [
    {
      "passenger_name": "John Doe",
      "country_code": "+1",
      "passenger_phone": "3051234567",
      "passenger_language": "en",
      "service_type_id": 1,
      "source": "123 Main St, Miami, FL 33101",
      "pickup_latitude": 25.7617,
      "pickup_longitude": -80.1918,
      "destination": "Jackson Memorial Hospital, 1611 NW 12th Ave, Miami, FL 33136",
      "dropoff_latitude": 25.7877,
      "dropoff_longitude": -80.2106,
      "pickup_date_time": "2025-12-05 09:00:00",
      "eta_time": null,
      "appointment_time": "2025-12-05 11:15:00",
      "special_note": "Wheelchair accessible",
      "return_trip_needed": "yes",
      "return_trip_type": "immediate"
    }
  ],
  "total_trips": 1,
  "processing_time_seconds": 3.2,
  "features_used": {
    "llm_enhancement": true,
    "geocoding": true,
    "geocoding_provider": "google"
  }
}
```

**Error responses:**

| Status | Body | Cause |
|--------|------|-------|
| 400 | `{"success": false, "error": "No file uploaded. Include file in multipart/form-data as \"file\""}` | Missing file field |
| 400 | `{"success": false, "error": "Empty filename"}` | Empty filename |
| 400 | `{"success": false, "error": "Invalid file type. Allowed: xlsx, xls"}` | Wrong file extension |
| 401 | `{"success": false, "error": "Missing X-API-Key header"}` | No auth header |
| 401 | `{"success": false, "error": "Invalid API key"}` | Wrong API key |
| 500 | `{"success": false, "error": "...", "error_type": "..."}` | Internal processing error |

---

### GET /api/status

Returns current server configuration. Requires authentication.

**Headers:**

| Header | Required | Description |
|--------|----------|-------------|
| `X-API-Key` | Yes | API authentication key |

**Example request:**

```bash
curl -H "X-API-Key: YOUR_API_KEY_HERE" \
  https://web-production-c09c8.up.railway.app/api/status
```

**Response (200):**

```json
{
  "success": true,
  "configuration": {
    "llm_available": true,
    "llm_enabled_by_default": false,
    "geocoding_enabled_by_default": true,
    "geocoding_provider": "google",
    "google_maps_available": true,
    "max_file_size_mb": 16.0,
    "allowed_extensions": ["xlsx", "xls"]
  }
}
```

---

## Trip Schema

Each object in the `trips` array has these fields:

| Field | Type | Description |
|-------|------|-------------|
| `passenger_name` | string | Passenger full name |
| `country_code` | string | Phone country code (default: "+1") |
| `passenger_phone` | string | Phone number, digits only |
| `passenger_language` | string | Language code: "en" or "es" |
| `service_type_id` | integer | 1=ambulatory, 7=wheelchair, 9=stretcher |
| `source` | string | Full pickup address |
| `pickup_latitude` | float or null | GPS latitude (requires geocoding) |
| `pickup_longitude` | float or null | GPS longitude (requires geocoding) |
| `destination` | string | Full dropoff address |
| `dropoff_latitude` | float or null | GPS latitude (requires geocoding) |
| `dropoff_longitude` | float or null | GPS longitude (requires geocoding) |
| `pickup_date_time` | string | Format: "YYYY-MM-DD HH:MM:SS" |
| `eta_time` | string or null | Estimated arrival time |
| `appointment_time` | string | Format: "YYYY-MM-DD HH:MM:SS" |
| `special_note` | string or null | Additional notes or requirements |
| `return_trip_needed` | string | "yes" or "no" |
| `return_trip_type` | string or null | "immediate" or "scheduled" |

---

## Processing Modes

| Parameter | Effect | Cost |
|-----------|--------|------|
| `use_llm=false, use_geocoding=false` | Basic parsing only | Free |
| `use_llm=false, use_geocoding=true` | Parsing + GPS coordinates | ~$0/trip (free tier) |
| `use_llm=true, use_geocoding=true` | Full AI parsing + GPS | ~$0.00025/trip |

---

## Rate Limits and Constraints

- Maximum file size: 16 MB
- Allowed file types: `.xlsx`, `.xls`
- Recommended client timeout: 120 seconds
- For files with 100+ trips, expect 30-60 seconds processing time

---

Back to [README](README.md).
