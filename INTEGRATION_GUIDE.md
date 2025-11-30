# NEMT Parser API - Integration Guide for Website Team

## Quick Start

Your parser API is live at: **`https://nemt-parser.up.railway.app/api/upload`**

---

## 🔑 Authentication

Add this header to all requests:
```
X-API-Key: nemt_parser_secret_key_2025
```

---

## 📡 API Endpoint

**URL:** `POST https://nemt-parser.up.railway.app/api/upload`

**Content-Type:** `multipart/form-data`

**Form Data:**
- `file` (required): Excel file (.xlsx or .xls)
- `clinic_id` (optional): Clinic identifier
- `use_geocoding` (optional): "true" or "false" (default: true)
- `use_llm` (optional): "true" or "false" (default: false)

---

## 💻 Integration Code Examples

### Python (Flask)

```python
import requests

PARSER_API_URL = "https://nemt-parser.up.railway.app/api/upload"
PARSER_API_KEY = "nemt_parser_secret_key_2025"

def process_clinic_upload(uploaded_file, clinic_id):
    """
    Process clinic Excel upload via parser API

    Args:
        uploaded_file: File object from request.files['file']
        clinic_id: Clinic identifier

    Returns:
        dict: {success: bool, trips: list, total_trips: int}
    """

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
            timeout=120  # 2 minute timeout
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


# Add this to your existing backend route:
@app.route('/api/clinic/upload', methods=['POST'])
def handle_clinic_upload():
    """Your existing upload endpoint"""

    # Get file from clinic's browser
    file = request.files['file']
    clinic_id = request.form.get('clinic_id')

    # Call parser API
    result = process_clinic_upload(file, clinic_id)

    if result['success']:
        # Save trips to your database
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

---

### Python (Django)

```python
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

PARSER_API_URL = "https://nemt-parser.up.railway.app/api/upload"
PARSER_API_KEY = "nemt_parser_secret_key_2025"

@csrf_exempt
def upload_clinic_trips(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    file = request.FILES.get('file')
    clinic_id = request.POST.get('clinic_id')

    if not file:
        return JsonResponse({'error': 'No file uploaded'}, status=400)

    # Call parser API
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

        # Save to Django models
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

---

### Node.js (Express)

```javascript
const axios = require('axios');
const FormData = require('form-data');

const PARSER_API_URL = 'https://nemt-parser.up.railway.app/api/upload';
const PARSER_API_KEY = 'nemt_parser_secret_key_2025';

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

// Add to your Express routes:
const multer = require('multer');
const upload = multer({ storage: multer.memoryStorage() });

app.post('/api/clinic/upload', upload.single('file'), async (req, res) => {
    const result = await processClinicUpload(req.file, req.body.clinic_id);

    if (result.success) {
        // Save to database
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

---

### PHP (Laravel)

```php
<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;

class TripController extends Controller
{
    const PARSER_API_URL = 'https://nemt-parser.up.railway.app/api/upload';
    const PARSER_API_KEY = 'nemt_parser_secret_key_2025';

    public function uploadClinicTrips(Request $request)
    {
        $file = $request->file('file');
        $clinicId = $request->input('clinic_id');

        // Call parser API
        $response = Http::withHeaders([
            'X-API-Key' => self::PARSER_API_KEY
        ])->timeout(120)->attach(
            'file', file_get_contents($file->getRealPath()), $file->getClientOriginalName()
        )->post(self::PARSER_API_URL, [
            'clinic_id' => $clinicId,
            'use_geocoding' => 'true'
        ]);

        if ($response->successful()) {
            $result = $response->json();

            // Save to database
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

## 📥 Request Example

```bash
curl -X POST https://nemt-parser.up.railway.app/api/upload \
  -H "X-API-Key: nemt_parser_secret_key_2025" \
  -F "file=@clinic_trips.xlsx" \
  -F "clinic_id=clinic_123" \
  -F "use_geocoding=true"
```

---

## 📤 Response Format

### Success Response (200)

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

### Error Response (400/401/500)

```json
{
  "success": false,
  "error": "Invalid file type. Allowed: xlsx, xls",
  "error_type": "ValidationError"
}
```

---

## 🗂️ Trip Data Schema

| Field | Type | Description |
|-------|------|-------------|
| `passenger_name` | string | Full name |
| `country_code` | string | Phone country code ("+1") |
| `passenger_phone` | string | Digits only |
| `passenger_language` | string | "en" or "es" |
| `service_type_id` | int | 1=ambulatory, 2=wheelchair, 3=stretcher |
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

## ⚙️ Optional Features

### Disable Geocoding (faster, but no coordinates)

```python
data = {
    'clinic_id': clinic_id,
    'use_geocoding': 'false'  # Skip geocoding
}
```

### Enable LLM Enhancement (better address cleaning)

```python
data = {
    'clinic_id': clinic_id,
    'use_llm': 'true'  # Use Claude AI to clean addresses
}
```

**Note:** LLM requires `ANTHROPIC_API_KEY` to be configured on the parser API.

---

## 🐛 Error Handling

### Common Errors

| Status | Error | Cause | Solution |
|--------|-------|-------|----------|
| 401 | "Missing X-API-Key header" | No auth header | Add `X-API-Key` header |
| 401 | "Invalid API key" | Wrong key | Use correct API key |
| 400 | "No file uploaded" | Missing file | Include `file` in form data |
| 400 | "Invalid file type" | Wrong extension | Use .xlsx or .xls only |
| 500 | Parser error | Internal error | Contact Erich |
| 504 | Timeout | File too large/slow | Increase timeout or split file |

### Recommended Error Handling

```python
try:
    result = process_clinic_upload(file, clinic_id)

    if result['success']:
        # Success - save to database
        for trip in result['trips']:
            db.save(trip)
    else:
        # Parser returned error
        log_error(f"Parser error: {result['error']}")
        notify_user("Failed to parse file")

except requests.exceptions.Timeout:
    # Parser took too long (>2 minutes)
    log_error("Parser timeout")
    notify_user("File is too large or complex")

except requests.exceptions.ConnectionError:
    # Cannot reach parser API
    log_error("Parser API unreachable")
    notify_user("Parser service temporarily unavailable")
```

---

## 📊 Performance

**Expected processing times:**

| Trips | Geocoding | LLM | Time |
|-------|-----------|-----|------|
| 10 | Yes | No | ~3-5 sec |
| 10 | Yes | Yes | ~8-12 sec |
| 50 | Yes | No | ~15-20 sec |
| 100 | Yes | No | ~30-40 sec |

**Recommendations:**
- Show loading indicator for user
- Set timeout to 120 seconds minimum
- For >100 trips, consider batching

---

## 🔒 Security Best Practices

1. **Never expose API key in frontend code**
   - ❌ Bad: `fetch(url, {headers: {'X-API-Key': 'secret'}})`
   - ✅ Good: Frontend → Your backend → Parser API

2. **Validate files before sending**
   ```python
   if not file.filename.endswith(('.xlsx', '.xls')):
       return {'error': 'Invalid file type'}, 400
   ```

3. **Limit file size**
   ```python
   if file.content_length > 16 * 1024 * 1024:  # 16MB
       return {'error': 'File too large'}, 400
   ```

4. **Authenticate clinics** before forwarding to parser

---

## 🧪 Testing

### Test with Sample File

Download sample: [ppol_example_small_clinic_messy.xlsx](https://github.com/Erichalfonso/nemt-trip-parser/blob/main/sample_data/)

### Test Request

```bash
curl -X POST https://nemt-parser.up.railway.app/api/upload \
  -H "X-API-Key: nemt_parser_secret_key_2025" \
  -F "file=@test_file.xlsx" \
  -F "clinic_id=test_clinic"
```

### Expected Response

Should return JSON with parsed trips in ~3-5 seconds.

---

## 📞 Support

**Issues with parser API?**
- Contact: Erich Alfonso
- GitHub Issues: https://github.com/Erichalfonso/nemt-trip-parser/issues

**Response time:** Usually within 24 hours

---

## 📈 Monitoring

### Health Check

```bash
curl https://nemt-parser.up.railway.app/health
```

Returns:
```json
{
  "status": "ok",
  "timestamp": "2025-11-29T12:00:00",
  "version": "1.0.0"
}
```

### Check Configuration

```bash
curl -H "X-API-Key: nemt_parser_secret_key_2025" \
  https://nemt-parser.up.railway.app/api/status
```

---

## 🚀 Quick Integration Checklist

- [ ] Read this guide
- [ ] Copy example code for your backend language
- [ ] Add API key to your environment variables
- [ ] Test with sample file
- [ ] Integrate into your upload endpoint
- [ ] Add error handling
- [ ] Test with real clinic data
- [ ] Deploy to production
- [ ] Monitor for errors

---

**You're all set!** The parser API is ready to integrate. 🎉
