# NEMT Trip Parser API

**Production-ready API for parsing NEMT (Non-Emergency Medical Transportation) trip data.**

Accepts messy clinic Excel files in any format and returns standardized JSON with GPS coordinates and cleaned addresses.

---

## 🚀 Live API

**Endpoint:** `https://web-production-c09c8.up.railway.app/api/upload`

**Status:** ✅ Deployed and running on Railway

---

## 📋 For Website Integration Team

**👉 Read the [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for complete API documentation.**

It includes:
- API endpoint and authentication
- Request/response formats
- Code examples (Python, Node.js, PHP)
- Error handling
- Testing instructions

---

## ✨ Features

- ✅ **Smart Excel Parsing**: Handles messy clinic data in any format
- ✅ **AI Enhancement**: Uses Claude to clean addresses and identify clinics
- ✅ **GPS Geocoding**: Converts addresses to latitude/longitude (Google Maps)
- ✅ **Flexible Input**: Handles various date/time/phone formats
- ✅ **RESTful API**: Simple HTTP endpoint, ready to integrate

---

## 🎯 Quick Test

```bash
curl -X POST https://web-production-c09c8.up.railway.app/api/upload \
  -H "X-API-Key: REDACTED_API_KEY" \
  -F "file=@your_clinic_file.xlsx" \
  -F "clinic_id=test_clinic" \
  -F "use_geocoding=true" \
  -F "use_llm=true"
```

**Response:**
```json
{
  "success": true,
  "trips": [
    {
      "passenger_name": "Juan G.",
      "passenger_phone": "3055550011",
      "source": "1230 NW 5th Street, Apartment 4B, Miami, FL 33125",
      "pickup_latitude": 25.7780827,
      "pickup_longitude": -80.2154498,
      "destination": "Jackson Cancer Center, 1611 NW 12th Avenue, Miami, FL 33136",
      "dropoff_latitude": 25.7957767,
      "dropoff_longitude": -80.2152613,
      "pickup_date_time": "2025-12-05 08:10:00",
      "appointment_time": "2025-12-05 09:00:00",
      "service_type_id": 2,
      "return_trip_needed": "yes",
      "return_trip_type": "immediate"
    }
  ],
  "total_trips": 3,
  "processing_time_seconds": 5.7
}
```

---

## 🏗️ Architecture

```
Website Backend → Parser API (Railway) → Standardized JSON
                      ↓
            Excel Upload → Parse → LLM Clean → Geocode → Response
```

### Processing Pipeline

1. **Parse Layer** - Extracts data from messy Excel formats
2. **LLM Enhancement** (optional) - Claude AI cleans addresses and identifies clinics
3. **Geocoding** (optional) - Google Maps converts addresses to GPS coordinates
4. **Response** - Returns standardized JSON

---

## 📊 Output Format

Each trip includes 17 standardized fields:

```json
{
  "passenger_name": "string",
  "country_code": "string",
  "passenger_phone": "string",
  "passenger_language": "string (en|es)",
  "service_type_id": "number (1=ambulatory, 2=wheelchair, 3=stretcher)",
  "source": "string (pickup address)",
  "pickup_latitude": "number | null",
  "pickup_longitude": "number | null",
  "destination": "string (dropoff address)",
  "dropoff_latitude": "number | null",
  "dropoff_longitude": "number | null",
  "pickup_date_time": "string (YYYY-MM-DD HH:MM:SS)",
  "eta_time": "string | null",
  "appointment_time": "string (YYYY-MM-DD HH:MM:SS)",
  "special_note": "string",
  "return_trip_needed": "string (yes|no)",
  "return_trip_type": "string (immediate|scheduled) | null"
}
```

---

## ⚙️ Configuration

### API Keys (Already Configured)

The API is pre-configured with:
- ✅ Google Maps API key (geocoding)
- ✅ Anthropic Claude API key (LLM enhancement)
- ✅ Parser authentication key

### Optional Request Parameters

Control features per request:

- `use_geocoding`: `"true"` or `"false"` (default: true)
- `use_llm`: `"true"` or `"false"` (default: false)
- `clinic_id`: String identifier for tracking

**Example:**
```bash
# Basic parsing only (fastest, no GPS coords)
use_geocoding=false use_llm=false

# With geocoding (adds GPS coordinates)
use_geocoding=true use_llm=false

# Full features (cleaned addresses + GPS)
use_geocoding=true use_llm=true
```

---

## 📈 Performance & Cost

| Mode | Processing Time | Cost per Trip | GPS Coords | Cleaned Addresses |
|------|----------------|---------------|------------|-------------------|
| Basic | 0.02s | $0 | ❌ | ❌ |
| + Geocoding | 1s | ~$0 (free tier) | ✅ | ❌ |
| + LLM + Geocoding | 5-6s | ~$0.00025 | ✅ | ✅ |

**Monthly Cost Estimate (1000 trips):**
- Google Maps: $0 (within $200 free tier)
- Claude API: ~$0.25
- **Total: < $1/month**

---

## 🔗 Additional Documentation

- **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** - Complete integration guide for website team
- **[RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)** - Deployment configuration and setup
- **[TEAM_HANDOFF.md](TEAM_HANDOFF.md)** - Project handoff documentation

---

## 🚀 Deployment

**Hosting:** Railway (https://railway.app/)

**Auto-Deploy:** ✅ Enabled
- Pushes to `main` branch automatically deploy
- Build time: ~2-3 minutes
- Zero downtime deployments

**Monitoring:**
- Health check: `GET https://web-production-c09c8.up.railway.app/health`
- Status: `GET https://web-production-c09c8.up.railway.app/api/status`
- Logs: Railway dashboard

---

## 🔐 Security

- ✅ API key authentication required (`X-API-Key` header)
- ✅ Private GitHub repository
- ✅ HTTPS enforced
- ✅ CORS enabled for cross-origin requests
- ✅ File size limits (16MB max)
- ✅ Allowed file types: `.xlsx`, `.xls` only

---

## 📞 Support

**Repository:** https://github.com/Erichalfonso/nemt-trip-parser (Private)

**Contact:** Erich

**Railway Dashboard:** https://railway.app/

---

## 📝 License

Proprietary - Internal company use only

---

**Ready to integrate!** 🎉

See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) to get started.
