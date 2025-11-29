# NEMT Trip Parser - API Documentation

## Overview

This API receives Excel files from clinics, intelligently parses them using AI-assisted column mapping, and returns standardized JSON trip data.

**Workflow:**
```
Clinic Excel → Your API → Parser (with AI mapping) → Standardized JSON
```

---

## Quick Start

### 1. Install & Run

```bash
pip install -r requirements.txt
python -m nemt_parser.integrations.flask_adapter
```

The API will run at `http://localhost:5000`

### 2. Upload an Excel File

```bash
curl -X POST http://localhost:5000/api/nemt/upload \
  -F "file=@clinic_trips.xlsx" \
  -F "clinic_id=miami_medical"
```

---

## API Endpoints

### 1. Upload Trip Data

**Endpoint:** `POST /api/nemt/upload`

**Description:** Upload Excel file with trip data. Returns parsed trips as JSON or requests mapping confirmation for new clinics.

**Request:**
```
Content-Type: multipart/form-data

Fields:
- file: Excel file (.xlsx, .xls)
- clinic_id: Unique clinic identifier (required)
- clinic_name: Human-readable clinic name (optional)
- user_id: User who uploaded (optional)
```

**Response (Success - Returning Clinic):**
```json
{
  "success": true,
  "trips_parsed": 15,
  "trips_saved": 15,
  "trips_failed": 0,
  "warnings": [],
  "trips": [
    {
      "patient_name": "John Smith",
      "patient_phone": "(305) 123-4567",
      "medicaid_id": "MCD123456789",
      "pickup_address": "123 Main St",
      "pickup_city": "Miami",
      "pickup_state": "FL",
      "pickup_zip": "33101",
      "dropoff_address": "999 Hospital Blvd",
      "dropoff_city": "Miami",
      "dropoff_state": "FL",
      "dropoff_zip": "33125",
      "appointment_date": "2025-01-15",
      "appointment_time": "09:00:00",
      "trip_type": "round_trip",
      "wheelchair": false,
      "stretcher": false,
      "ambulatory": true,
      "notes": "Patient needs assistance walking",
      "source_clinic_id": "miami_medical",
      "uploaded_at": "2025-01-10T14:30:00"
    }
    // ... up to first 10 trips in response
  ]
}
```

**Response (First-Time Clinic - Needs Mapping):**
```json
{
  "success": false,
  "needs_mapping": true,
  "detected_columns": [
    "Patient Name",
    "Medicaid #",
    "Pick-up Address",
    "Pick-up City",
    "Pick-up ZIP",
    "Drop-off Address",
    "Drop-off City",
    "Drop-off ZIP",
    "Appt Date",
    "Appt Time",
    "Wheelchair?"
  ],
  "suggested_mapping": {
    "clinic_id": "miami_medical",
    "clinic_name": "Miami Medical Center",
    "patient_name": "Patient Name",
    "medicaid_id": "Medicaid #",
    "pickup_address": "Pick-up Address",
    "pickup_city": "Pick-up City",
    "pickup_zip": "Pick-up ZIP",
    "dropoff_address": "Drop-off Address",
    "dropoff_city": "Drop-off City",
    "dropoff_zip": "Drop-off ZIP",
    "appointment_date": "Appt Date",
    "appointment_time": "Appt Time",
    "wheelchair": "Wheelchair?"
  },
  "message": "Please review and confirm the column mapping"
}
```

**Response (Error):**
```json
{
  "success": false,
  "errors": ["Error message"],
  "warnings": ["Warning message"]
}
```

**Example cURL:**
```bash
curl -X POST http://localhost:5000/api/nemt/upload \
  -F "file=@sample_data/clinic_a_trips.xlsx" \
  -F "clinic_id=miami_medical" \
  -F "clinic_name=Miami Medical Center"
```

**Example Python:**
```python
import requests

url = "http://localhost:5000/api/nemt/upload"
files = {"file": open("clinic_trips.xlsx", "rb")}
data = {
    "clinic_id": "miami_medical",
    "clinic_name": "Miami Medical Center"
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

---

### 2. Save/Confirm Mapping

**Endpoint:** `POST /api/nemt/mapping/save`

**Description:** Save or update column mapping for a clinic. Use this after reviewing the suggested mapping from first upload.

**Request:**
```json
Content-Type: application/json

{
  "clinic_id": "miami_medical",
  "clinic_name": "Miami Medical Center",
  "patient_name": "Patient Name",
  "medicaid_id": "Medicaid #",
  "pickup_address": "Pick-up Address",
  "pickup_city": "Pick-up City",
  "pickup_zip": "Pick-up ZIP",
  "dropoff_address": "Drop-off Address",
  "dropoff_city": "Drop-off City",
  "dropoff_zip": "Drop-off ZIP",
  "appointment_date": "Appt Date",
  "appointment_time": "Appt Time",
  "wheelchair": "Wheelchair?"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Mapping saved successfully",
  "clinic_id": "miami_medical"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/nemt/mapping/save \
  -H "Content-Type: application/json" \
  -d '{
    "clinic_id": "miami_medical",
    "patient_name": "Patient Name",
    "medicaid_id": "Medicaid #",
    "pickup_address": "Pick-up Address",
    "pickup_city": "Pick-up City",
    "pickup_zip": "Pick-up ZIP",
    "dropoff_address": "Drop-off Address",
    "dropoff_city": "Drop-off City",
    "dropoff_zip": "Drop-off ZIP",
    "appointment_date": "Appt Date"
  }'
```

---

### 3. Get Clinic Mapping

**Endpoint:** `GET /api/nemt/mapping/<clinic_id>`

**Description:** Retrieve saved mapping for a clinic.

**Response:**
```json
{
  "success": true,
  "mapping": {
    "clinic_id": "miami_medical",
    "clinic_name": "Miami Medical Center",
    "patient_name": "Patient Name",
    "medicaid_id": "Medicaid #",
    // ... all mapped fields
    "created_at": "2025-01-10T10:00:00",
    "updated_at": "2025-01-10T10:00:00"
  }
}
```

**Example:**
```bash
curl http://localhost:5000/api/nemt/mapping/miami_medical
```

---

### 4. List All Clinics

**Endpoint:** `GET /api/nemt/clinics`

**Description:** Get list of all clinics with saved mappings.

**Response:**
```json
{
  "success": true,
  "count": 3,
  "clinics": [
    {
      "clinic_id": "miami_medical",
      "clinic_name": "Miami Medical Center",
      "updated_at": "2025-01-10T10:00:00"
    },
    {
      "clinic_id": "orlando_clinic",
      "clinic_name": "Orlando Clinic",
      "updated_at": "2025-01-09T15:30:00"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:5000/api/nemt/clinics
```

---

### 5. Get Upload History

**Endpoint:** `GET /api/nemt/history`

**Description:** Get upload history with statistics.

**Query Parameters:**
- `clinic_id` (optional): Filter by clinic
- `limit` (optional): Max results (default: 50)

**Response:**
```json
{
  "success": true,
  "uploads": [
    {
      "id": 1,
      "clinic_id": "miami_medical",
      "filename": "clinic_a_trips.xlsx",
      "total_rows": 15,
      "successful_rows": 15,
      "failed_rows": 0,
      "uploaded_at": "2025-01-10T14:30:00",
      "errors": null,
      "warnings": []
    }
  ]
}
```

**Example:**
```bash
# All uploads
curl http://localhost:5000/api/nemt/history

# Specific clinic
curl "http://localhost:5000/api/nemt/history?clinic_id=miami_medical&limit=10"
```

---

## Integration with Your Existing Website

### Option 1: Python Backend (Flask/Django/FastAPI)

If you already have a Python backend:

```python
# In your existing upload handler
from nemt_parser import TripParser, MappingRepository

def handle_upload(excel_file, clinic_id):
    # Initialize parser
    repo = MappingRepository("postgresql://user:pass@localhost/mydb")
    parser = TripParser(mapping_repository=repo)

    # Parse file
    result = parser.parse_excel(excel_file, clinic_id=clinic_id)

    # Return JSON
    return {
        "trips": [trip.model_dump() for trip in result.trips],
        "success": result.success
    }
```

### Option 2: Standalone Microservice

Run the parser as a separate microservice:

```bash
# Start the Flask API
python -m nemt_parser.integrations.flask_adapter

# Your main website calls it via HTTP
POST http://parser-service:5000/api/nemt/upload
```

### Option 3: Direct Integration

Import and use directly in your codebase:

```python
from nemt_parser import TripParser, MappingRepository

# Use in your Django/Flask/FastAPI views
```

---

## Standardized Trip JSON Schema

All trips are returned in this consistent format:

```json
{
  "patient_name": "string (required)",
  "patient_phone": "string (optional)",
  "medicaid_id": "string (required)",
  "date_of_birth": "YYYY-MM-DD (optional)",

  "pickup_address": "string (required)",
  "pickup_city": "string (required)",
  "pickup_state": "string (default: FL)",
  "pickup_zip": "string (required)",

  "dropoff_address": "string (required)",
  "dropoff_city": "string (required)",
  "dropoff_state": "string (default: FL)",
  "dropoff_zip": "string (required)",

  "appointment_date": "YYYY-MM-DD (required)",
  "appointment_time": "HH:MM:SS (optional)",

  "trip_type": "pickup | return | round_trip",
  "wheelchair": "boolean",
  "stretcher": "boolean",
  "ambulatory": "boolean",

  "notes": "string (optional)",
  "appointment_type": "string (optional)",
  "clinic_name": "string (optional)",

  "source_clinic_id": "string",
  "uploaded_at": "ISO 8601 datetime"
}
```

---

## Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error message",
  "errors": ["Detailed error 1", "Detailed error 2"],
  "warnings": ["Warning 1"]
}
```

**Common HTTP Status Codes:**
- `200`: Success
- `400`: Bad request (invalid file, missing parameters)
- `404`: Resource not found (e.g., clinic mapping)
- `500`: Server error

---

## Testing

Test the API with the provided sample files:

```bash
cd nemt-trip-parser

# Test first-time clinic (will request mapping)
curl -X POST http://localhost:5000/api/nemt/upload \
  -F "file=@sample_data/clinic_a_trips.xlsx" \
  -F "clinic_id=test_clinic_a"

# Save the suggested mapping
curl -X POST http://localhost:5000/api/nemt/mapping/save \
  -H "Content-Type: application/json" \
  -d @sample_mapping.json

# Upload again (will auto-parse)
curl -X POST http://localhost:5000/api/nemt/upload \
  -F "file=@sample_data/clinic_a_trips_week2.xlsx" \
  -F "clinic_id=test_clinic_a"
```

---

## Database Configuration

By default, uses SQLite. For production, use PostgreSQL:

```python
# In your Flask app config
app.config['NEMT_DATABASE_URL'] = 'postgresql://user:pass@localhost/nemt_db'
```

Supported databases:
- SQLite: `sqlite:///nemt_trips.db`
- PostgreSQL: `postgresql://user:pass@host/db`
- MySQL: `mysql://user:pass@host/db`

---

## Next Steps

1. ✅ **Test with sample data** - Use the provided Excel files
2. ✅ **Integrate into your website** - Add the API endpoints
3. ⚙️ **Configure database** - Set up PostgreSQL for production
4. 🎨 **Build UI** - Create frontend for mapping review
5. 🤖 **Optional: Add LLM** - Enhance mapping suggestions with Claude/GPT

---

For questions or issues, check the examples in `/examples` directory.
