# NEMT Trip Parser - Team Handoff Documentation

## 🎉 **Project Complete!**

The NEMT Trip Parser API is ready for integration with your website.

---

## 📍 **Repository**

```
https://github.com/Erichalfonso/nemt-trip-parser
```

Clone it:
```bash
git clone https://github.com/Erichalfonso/nemt-trip-parser.git
```

---

## 🚀 **Quick Start**

### **1. Install Dependencies**

```bash
cd nemt-trip-parser
pip install -r requirements.txt
```

### **2. Configure Environment**

Create `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
GOOGLE_MAPS_API_KEY=your-google-maps-key-here
ANTHROPIC_API_KEY=your-claude-key-here
PARSER_API_KEY=your-secret-authentication-key

USE_LLM=false
USE_GEOCODING=true
GEOCODING_PROVIDER=google
```

### **3. Start the Server**

**Development:**
```bash
python api_server.py
```

**Production (recommended):**
```bash
gunicorn -w 4 -b 0.0.0.0:5001 api_server:app
```

Server runs on: `http://localhost:5001`

---

## 📡 **API Endpoints**

### **GET /health**
Health check endpoint (no authentication required)

**Response:**
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

### **POST /api/upload**
Upload Excel file and get standardized JSON

**Headers:**
```
X-API-Key: your-secret-api-key
```

**Request (multipart/form-data):**
- `file`: Excel file (.xlsx or .xls)
- `clinic_id`: Clinic identifier (string, optional)
- `use_llm`: Enable LLM enhancement ("true" or "false", optional)
- `use_geocoding`: Enable geocoding ("true" or "false", optional)

**Response (Success):**
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

**Response (Error):**
```json
{
  "success": false,
  "error": "Invalid file type. Allowed: xlsx, xls",
  "error_type": "ValidationError"
}
```

---

### **GET /api/status**
Get API configuration (requires authentication)

**Headers:**
```
X-API-Key: your-secret-api-key
```

**Response:**
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

## 💻 **Integration Examples**

### **Python (requests)**

```python
import requests

url = "http://your-server:5001/api/upload"
headers = {"X-API-Key": "your-secret-key"}

files = {"file": open("clinic_data.xlsx", "rb")}
data = {
    "clinic_id": "clinic_123",
    "use_geocoding": "true"
}

response = requests.post(url, headers=headers, files=files, data=data)

if response.status_code == 200:
    result = response.json()
    trips = result["trips"]
    print(f"Parsed {len(trips)} trips successfully")
else:
    print(f"Error: {response.json()}")
```

### **JavaScript (fetch)**

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('clinic_id', 'clinic_123');
formData.append('use_geocoding', 'true');

fetch('http://your-server:5001/api/upload', {
    method: 'POST',
    headers: {
        'X-API-Key': 'your-secret-key'
    },
    body: formData
})
.then(res => res.json())
.then(data => {
    if (data.success) {
        console.log(`Parsed ${data.total_trips} trips`);
        console.log(data.trips);
    } else {
        console.error('Error:', data.error);
    }
});
```

### **cURL**

```bash
curl -X POST http://localhost:5001/api/upload \
  -H "X-API-Key: your-secret-key" \
  -F "file=@clinic_data.xlsx" \
  -F "clinic_id=clinic_123" \
  -F "use_geocoding=true"
```

---

## 🗂️ **JSON Output Schema**

Every trip in the `trips` array has these fields:

| Field | Type | Description |
|-------|------|-------------|
| `passenger_name` | string | Passenger full name |
| `country_code` | string | Phone country code (default: "+1") |
| `passenger_phone` | string | Phone number (digits only) |
| `passenger_language` | string | Language code ("en" or "es") |
| `service_type_id` | integer | 1=ambulatory, 2=wheelchair, 3=stretcher |
| `source` | string | Pickup address (full) |
| `pickup_latitude` | float \| null | Pickup GPS latitude |
| `pickup_longitude` | float \| null | Pickup GPS longitude |
| `destination` | string | Dropoff address (full) |
| `dropoff_latitude` | float \| null | Dropoff GPS latitude |
| `dropoff_longitude` | float \| null | Dropoff GPS longitude |
| `pickup_date_time` | string | Pickup datetime (YYYY-MM-DD HH:MM:SS) |
| `eta_time` | string \| null | Estimated arrival time |
| `appointment_time` | string | Appointment datetime (YYYY-MM-DD HH:MM:SS) |
| `special_note` | string \| null | Additional notes/requirements |
| `return_trip_needed` | string | "yes" or "no" |
| `return_trip_type` | string \| null | "immediate" or "scheduled" |

---

## 🔐 **Security**

1. **API Key Authentication**: All endpoints (except `/health`) require `X-API-Key` header
2. **File Size Limit**: 16MB maximum
3. **File Type Validation**: Only `.xlsx` and `.xls` allowed
4. **HTTPS**: Use HTTPS in production (configure via nginx/Apache)

**Recommended production setup:**
```
[Website] → HTTPS → [Nginx Reverse Proxy] → HTTP → [Gunicorn API Server]
```

---

## 📊 **Features**

### **Smart Parsing**
- Handles messy Excel formats automatically
- Parses various date/time formats
- Cleans phone numbers
- Detects service type from notes
- Extracts language preference

### **LLM Enhancement (Optional)**
- Uses Claude AI to clean addresses
- Infers full clinic addresses from partial names
- Standardizes formatting
- **Cost**: ~$0.00025 per trip

### **Geocoding (Optional)**
- **Google Maps**: Most accurate, requires API key, $0.005 per address
- **OpenStreetMap**: Free, slightly less accurate, 1 req/sec limit

---

## 🚀 **Deployment Options**

### **Option 1: Same Server as Website**
Run on same machine, different port

```bash
gunicorn -w 4 -b 0.0.0.0:5001 api_server:app
```

Your website calls: `http://localhost:5001/api/upload`

### **Option 2: Separate Server**
Deploy to separate machine (AWS EC2, DigitalOcean, etc.)

```bash
# On parser server
gunicorn -w 4 -b 0.0.0.0:5001 api_server:app
```

Your website calls: `http://parser-server-ip:5001/api/upload`

### **Option 3: Docker**
```bash
docker build -t nemt-parser .
docker run -p 5001:5001 \
  -e GOOGLE_MAPS_API_KEY=xxx \
  -e PARSER_API_KEY=xxx \
  nemt-parser
```

### **Option 4: Cloud Functions (AWS Lambda, etc.)**
See `deployment/` folder for cloud-specific configurations

---

## 🐛 **Troubleshooting**

### **Error: "Missing X-API-Key header"**
- Add `X-API-Key` to request headers
- Verify key matches `.env` file

### **Error: "Invalid file type"**
- Only `.xlsx` and `.xls` files supported
- Check file extension

### **Geocoding not working**
- Verify `GOOGLE_MAPS_API_KEY` is set in `.env`
- Check Google Cloud Console: Geocoding API enabled + billing enabled
- Try `use_geocoding=false` to test without geocoding

### **LLM enhancement failing**
- Verify `ANTHROPIC_API_KEY` is set in `.env`
- Check API key is valid at https://console.anthropic.com/
- Try `use_llm=false` to test without LLM

---

## 💰 **Cost Estimation**

**Monthly Usage: 1,000 trips**

| Service | Cost |
|---------|------|
| Google Geocoding (2 addresses per trip) | $10 |
| Claude LLM Enhancement (optional) | $0.25 |
| Server hosting | $5-20 |
| **Total** | **$15-30/month** |

**Note**: Google provides $200/month free credit, so geocoding is often FREE!

---

##⚙️ **Configuration Options**

Edit `.env` file:

```env
# Required
GOOGLE_MAPS_API_KEY=your-key
PARSER_API_KEY=your-secret-key

# Optional
ANTHROPIC_API_KEY=your-claude-key  # For LLM enhancement
USE_LLM=false                       # Enable LLM by default
USE_GEOCODING=true                  # Enable geocoding by default
GEOCODING_PROVIDER=google           # "google" or "osm"
```

---

## 📞 **Support**

**Developer**: Erich Alfonso
**Repository**: https://github.com/Erichalfonso/nemt-trip-parser
**Issues**: https://github.com/Erichalfonso/nemt-trip-parser/issues

---

## 📝 **License**

MIT License - See LICENSE file

---

## 🎯 **Quick Integration Checklist**

- [ ] Clone repository
- [ ] Install dependencies (`pip install -r requirements.txt`)
- [ ] Configure `.env` with API keys
- [ ] Start server (`python api_server.py` or `gunicorn`)
- [ ] Test health endpoint (`curl http://localhost:5001/health`)
- [ ] Test upload with sample file
- [ ] Integrate into website backend
- [ ] Deploy to production server
- [ ] Configure HTTPS/reverse proxy
- [ ] Monitor logs and errors

---

**You're all set! The parser is ready for your team to integrate.** 🚀
