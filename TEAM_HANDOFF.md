# Team Handoff

Deployment, configuration, and operational reference for the NEMT Trip Parser.

---

## Repository

```
https://github.com/Erichalfonso/nemt-trip-parser
```

```bash
git clone https://github.com/Erichalfonso/nemt-trip-parser.git
```

---

## Quick Start

### 1. Install dependencies

```bash
cd nemt-trip-parser
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
API_KEY=your-secure-authentication-key
GOOGLE_MAPS_API_KEY=your-google-maps-key
ANTHROPIC_API_KEY=your-claude-key

USE_LLM=false
USE_GEOCODING=true
GEOCODING_PROVIDER=google
```

### 3. Start the server

**Development:**

```bash
python api_server.py
```

**Production:**

```bash
gunicorn -w 4 -b 0.0.0.0:5001 api_server:app
```

Server runs on `http://localhost:5001`.

---

## API Endpoints

### GET /health

Health check (no authentication required).

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

### POST /api/upload

Upload Excel file and receive standardized JSON. Requires `X-API-Key` header.

**Request:** `multipart/form-data` with fields `file`, `clinic_id`, `use_llm`, `use_geocoding`.

**Response:**

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
    "llm_enhancement": false,
    "geocoding": true,
    "geocoding_provider": "google"
  }
}
```

### GET /api/status

Returns server configuration. Requires `X-API-Key` header.

---

## Integration Examples

### Python

```python
import requests
import os

url = "http://your-server:5001/api/upload"
headers = {"X-API-Key": os.getenv("API_KEY")}

files = {"file": open("clinic_data.xlsx", "rb")}
data = {
    "clinic_id": "clinic_123",
    "use_geocoding": "true"
}

response = requests.post(url, headers=headers, files=files, data=data)

if response.status_code == 200:
    result = response.json()
    trips = result["trips"]
    print(f"Parsed {len(trips)} trips")
```

### JavaScript

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('clinic_id', 'clinic_123');
formData.append('use_geocoding', 'true');

fetch('http://your-server:5001/api/upload', {
    method: 'POST',
    headers: { 'X-API-Key': apiKey },
    body: formData
})
.then(res => res.json())
.then(data => {
    if (data.success) {
        console.log(`Parsed ${data.total_trips} trips`);
    }
});
```

### cURL

```bash
curl -X POST http://localhost:5001/api/upload \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -F "file=@clinic_data.xlsx" \
  -F "clinic_id=clinic_123" \
  -F "use_geocoding=true"
```

---

## JSON Output Schema

| Field | Type | Description |
|-------|------|-------------|
| `passenger_name` | string | Passenger full name |
| `country_code` | string | Phone country code (default: "+1") |
| `passenger_phone` | string | Phone number (digits only) |
| `passenger_language` | string | Language code ("en" or "es") |
| `service_type_id` | integer | 1=ambulatory, 7=wheelchair, 9=stretcher |
| `source` | string | Pickup address (full) |
| `pickup_latitude` | float/null | Pickup GPS latitude |
| `pickup_longitude` | float/null | Pickup GPS longitude |
| `destination` | string | Dropoff address (full) |
| `dropoff_latitude` | float/null | Dropoff GPS latitude |
| `dropoff_longitude` | float/null | Dropoff GPS longitude |
| `pickup_date_time` | string | Pickup datetime (YYYY-MM-DD HH:MM:SS) |
| `eta_time` | string/null | Estimated arrival time |
| `appointment_time` | string | Appointment datetime (YYYY-MM-DD HH:MM:SS) |
| `special_note` | string/null | Additional notes/requirements |
| `return_trip_needed` | string | "yes" or "no" |
| `return_trip_type` | string/null | "immediate" or "scheduled" |

---

## AI Features

- **Smart Column Detection:** Claude analyzes headers + sample rows to auto-map any Excel format (1 LLM call per file).
- **Address Cleaning:** Expands abbreviated addresses to full standardized form.
- **Service Type Inference:** Detects wheelchair/stretcher/ambulatory from free-text notes.
- **Multi-Format Parsing:** Handles diverse date, time, and phone formats.
- **GPS Geocoding:** Google Maps or OpenStreetMap address-to-coordinate conversion.

---

## Security

1. **API Key Authentication:** All endpoints except `/health` require the `X-API-Key` header.
2. **File Validation:** Only `.xlsx` and `.xls` files accepted, 16 MB max.
3. **HTTPS:** Use HTTPS in production (Railway handles this automatically).

Recommended architecture:

```
[Website] -- HTTPS --> [Reverse Proxy] -- HTTP --> [Gunicorn API Server]
```

---

## Deployment

### Railway (current)

See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md).

### Same server as website

```bash
gunicorn -w 4 -b 0.0.0.0:5001 api_server:app
```

Your website calls `http://localhost:5001/api/upload`.

### Separate server

Deploy to a dedicated machine and call `http://parser-server:5001/api/upload`.

### Docker

```bash
docker build -t nemt-parser .
docker run -p 5001:5001 \
  -e API_KEY=your-key \
  -e GOOGLE_MAPS_API_KEY=your-key \
  nemt-parser
```

---

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| "Missing X-API-Key header" | No auth header | Add `X-API-Key` to request headers |
| "Invalid API key" | Wrong key | Check key matches `API_KEY` env var |
| "Invalid file type" | Wrong extension | Use .xlsx or .xls only |
| Geocoding returns null | Missing API key | Set `GOOGLE_MAPS_API_KEY` and enable Geocoding API |
| LLM parsing fails | Missing API key | Set `ANTHROPIC_API_KEY` and verify at console.anthropic.com |

---

## Cost Estimate (1,000 trips/month)

| Service | Cost |
|---------|------|
| Google Geocoding | $0 (within $200/month free tier) |
| Claude LLM (optional) | ~$0.25 |
| Railway hosting | $5 |
| **Total** | **~$5.25/month** |

---

## Configuration Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `API_KEY` | Yes | Authentication key for requests |
| `GOOGLE_MAPS_API_KEY` | No | Google Maps geocoding |
| `ANTHROPIC_API_KEY` | No | Claude AI for smart parsing |
| `USE_LLM` | No | Default LLM setting (default: false) |
| `USE_GEOCODING` | No | Default geocoding setting (default: true) |
| `GEOCODING_PROVIDER` | No | "google" or "osm" (default: google) |

---

## License

MIT License. See [LICENSE](LICENSE).

---

Back to [README](README.md).
