# Integration Guide

How to connect your website backend to the NEMT Trip Parser API.

**API endpoint:** `https://web-production-c09c8.up.railway.app/api/upload`

---

## Authentication

Include this header in all requests:

```
X-API-Key: YOUR_API_KEY_HERE
```

Store the key in your environment variables. Never expose it in frontend code.

---

## API Endpoint

**URL:** `POST https://web-production-c09c8.up.railway.app/api/upload`

**Content-Type:** `multipart/form-data`

**Form fields:**
- `file` (required): Excel file (.xlsx or .xls)
- `clinic_id` (optional): Clinic identifier string
- `use_geocoding` (optional): "true" or "false" (default: "true")
- `use_llm` (optional): "true" or "false" (default: "false")

---

## Code Examples

### Python (Flask)

```python
import requests
import os

PARSER_API_URL = "https://web-production-c09c8.up.railway.app/api/upload"
PARSER_API_KEY = os.getenv("PARSER_API_KEY", "YOUR_API_KEY_HERE")

def process_clinic_upload(uploaded_file, clinic_id):
    files = {
        'file': (
            uploaded_file.filename,
            uploaded_file.stream,
            uploaded_file.content_type
        )
    }

    data = {
        'clinic_id': clinic_id,
        'use_geocoding': 'true'
    }

    headers = {
        'X-API-Key': PARSER_API_KEY
    }

    try:
        response = requests.post(
            PARSER_API_URL,
            files=files,
            data=data,
            headers=headers,
            timeout=120
        )

        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'trips': result['trips'],
                'total_trips': result['total_trips'],
                'processing_time': result['processing_time_seconds']
            }
        else:
            error_data = response.json()
            return {
                'success': False,
                'error': error_data.get('error', 'Parser API failed')
            }

    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Parser API timeout'}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'error': 'Cannot connect to parser API'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@app.route('/api/clinic/upload', methods=['POST'])
def handle_clinic_upload():
    file = request.files['file']
    clinic_id = request.form.get('clinic_id')

    result = process_clinic_upload(file, clinic_id)

    if result['success']:
        for trip in result['trips']:
            db.trips.insert(trip)

        return {
            'success': True,
            'total_trips': result['total_trips'],
            'message': f"Successfully parsed {result['total_trips']} trips"
        }, 200
    else:
        return {
            'success': False,
            'error': result['error']
        }, 500
```

### Python (Django)

```python
import requests
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

PARSER_API_URL = "https://web-production-c09c8.up.railway.app/api/upload"
PARSER_API_KEY = os.getenv("PARSER_API_KEY", "YOUR_API_KEY_HERE")

@csrf_exempt
def upload_clinic_trips(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    file = request.FILES.get('file')
    clinic_id = request.POST.get('clinic_id')

    if not file:
        return JsonResponse({'error': 'No file uploaded'}, status=400)

    files = {'file': (file.name, file.read(), file.content_type)}
    data = {'clinic_id': clinic_id, 'use_geocoding': 'true'}
    headers = {'X-API-Key': PARSER_API_KEY}

    response = requests.post(
        PARSER_API_URL,
        files=files,
        data=data,
        headers=headers,
        timeout=120
    )

    if response.status_code == 200:
        result = response.json()

        from .models import Trip
        for trip_data in result['trips']:
            Trip.objects.create(**trip_data)

        return JsonResponse({
            'success': True,
            'total_trips': result['total_trips']
        })
    else:
        return JsonResponse({
            'success': False,
            'error': response.json().get('error', 'Parser failed')
        }, status=500)
```

### Node.js (Express)

```javascript
const axios = require('axios');
const FormData = require('form-data');

const PARSER_API_URL = 'https://web-production-c09c8.up.railway.app/api/upload';
const PARSER_API_KEY = process.env.PARSER_API_KEY || 'YOUR_API_KEY_HERE';

async function processClinicUpload(file, clinicId) {
    const formData = new FormData();
    formData.append('file', file.buffer, file.originalname);
    formData.append('clinic_id', clinicId);
    formData.append('use_geocoding', 'true');

    try {
        const response = await axios.post(PARSER_API_URL, formData, {
            headers: {
                ...formData.getHeaders(),
                'X-API-Key': PARSER_API_KEY
            },
            timeout: 120000,
            maxContentLength: Infinity,
            maxBodyLength: Infinity
        });

        return {
            success: true,
            trips: response.data.trips,
            total_trips: response.data.total_trips
        };
    } catch (error) {
        return {
            success: false,
            error: error.response?.data?.error || error.message
        };
    }
}

const multer = require('multer');
const upload = multer({ storage: multer.memoryStorage() });

app.post('/api/clinic/upload', upload.single('file'), async (req, res) => {
    const result = await processClinicUpload(req.file, req.body.clinic_id);

    if (result.success) {
        const Trip = require('./models/Trip');
        await Trip.insertMany(result.trips);

        res.json({
            success: true,
            total_trips: result.total_trips
        });
    } else {
        res.status(500).json({
            success: false,
            error: result.error
        });
    }
});
```

### PHP (Laravel)

```php
<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;

class TripController extends Controller
{
    const PARSER_API_URL = 'https://web-production-c09c8.up.railway.app/api/upload';

    public function uploadClinicTrips(Request $request)
    {
        $file = $request->file('file');
        $clinicId = $request->input('clinic_id');
        $apiKey = config('services.nemt_parser.key');

        $response = Http::withHeaders([
            'X-API-Key' => $apiKey
        ])->timeout(120)->attach(
            'file', file_get_contents($file->getRealPath()), $file->getClientOriginalName()
        )->post(self::PARSER_API_URL, [
            'clinic_id' => $clinicId,
            'use_geocoding' => 'true'
        ]);

        if ($response->successful()) {
            $result = $response->json();

            foreach ($result['trips'] as $tripData) {
                Trip::create($tripData);
            }

            return response()->json([
                'success' => true,
                'total_trips' => $result['total_trips']
            ]);
        } else {
            return response()->json([
                'success' => false,
                'error' => $response->json()['error'] ?? 'Parser failed'
            ], 500);
        }
    }
}
```

---

## Response Format

### Success (200)

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
  "total_trips": 10,
  "processing_time_seconds": 3.2,
  "features_used": {
    "llm_enhancement": false,
    "geocoding": true,
    "geocoding_provider": "google"
  }
}
```

### Error (400/401/500)

```json
{
  "success": false,
  "error": "Invalid file type. Allowed: xlsx, xls",
  "error_type": "ValidationError"
}
```

---

## Trip Data Schema

| Field | Type | Description |
|-------|------|-------------|
| `passenger_name` | string | Full name |
| `country_code` | string | Phone country code ("+1") |
| `passenger_phone` | string | Digits only |
| `passenger_language` | string | "en" or "es" |
| `service_type_id` | int | 1=ambulatory, 7=wheelchair, 9=stretcher |
| `source` | string | Full pickup address |
| `pickup_latitude` | float/null | GPS latitude |
| `pickup_longitude` | float/null | GPS longitude |
| `destination` | string | Full dropoff address |
| `dropoff_latitude` | float/null | GPS latitude |
| `dropoff_longitude` | float/null | GPS longitude |
| `pickup_date_time` | string | "YYYY-MM-DD HH:MM:SS" |
| `eta_time` | string/null | Estimated arrival |
| `appointment_time` | string | "YYYY-MM-DD HH:MM:SS" |
| `special_note` | string/null | Additional notes |
| `return_trip_needed` | string | "yes" or "no" |
| `return_trip_type` | string/null | "immediate" or "scheduled" |

---

## Optional Features

### Disable geocoding (faster, no coordinates)

```python
data = {
    'clinic_id': clinic_id,
    'use_geocoding': 'false'
}
```

### Enable LLM enhancement (better address cleaning)

```python
data = {
    'clinic_id': clinic_id,
    'use_llm': 'true'
}
```

LLM requires `ANTHROPIC_API_KEY` configured on the server.

---

## Error Handling

| Status | Error | Cause | Solution |
|--------|-------|-------|----------|
| 401 | "Missing X-API-Key header" | No auth header | Add `X-API-Key` header |
| 401 | "Invalid API key" | Wrong key | Check your API key |
| 400 | "No file uploaded" | Missing file | Include `file` in form data |
| 400 | "Invalid file type" | Wrong extension | Use .xlsx or .xls only |
| 500 | Internal error | Processing failure | Check file format, contact support |
| 504 | Timeout | Large file or slow processing | Increase timeout or split file |

Recommended error handling pattern:

```python
try:
    result = process_clinic_upload(file, clinic_id)

    if result['success']:
        for trip in result['trips']:
            db.save(trip)
    else:
        log_error(f"Parser error: {result['error']}")

except requests.exceptions.Timeout:
    log_error("Parser timeout")

except requests.exceptions.ConnectionError:
    log_error("Parser API unreachable")
```

---

## Performance

| Trips | Geocoding | LLM | Expected Time |
|-------|-----------|-----|---------------|
| 10 | Yes | No | 3-5 sec |
| 10 | Yes | Yes | 8-12 sec |
| 50 | Yes | No | 15-20 sec |
| 100 | Yes | No | 30-40 sec |

Set client timeout to 120 seconds minimum. Show a loading indicator for users.

---

## Security

1. Never expose the API key in frontend code. Route requests through your backend.
2. Validate files before forwarding: check extension and size.
3. Authenticate your own users before calling the parser API.

---

## Testing

```bash
curl -X POST https://web-production-c09c8.up.railway.app/api/upload \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -F "file=@test_file.xlsx" \
  -F "clinic_id=test_clinic"
```

### Health check

```bash
curl https://web-production-c09c8.up.railway.app/health
```

### Configuration check

```bash
curl -H "X-API-Key: YOUR_API_KEY_HERE" \
  https://web-production-c09c8.up.railway.app/api/status
```

---

## Integration Checklist

- [ ] Copy example code for your backend language
- [ ] Store API key in environment variables
- [ ] Test with sample Excel file
- [ ] Integrate into your upload endpoint
- [ ] Add error handling and timeouts
- [ ] Test with real clinic data
- [ ] Deploy and monitor

---

Back to [README](README.md).
