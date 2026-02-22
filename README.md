# NEMT Trip Parser — AI-Powered

An AI-powered API that transforms messy clinic Excel files into standardized NEMT trip JSON with GPS coordinates. Upload any spreadsheet format — the AI figures out the rest.

---

## The Problem

Every clinic sends trip data in a different Excel format:

```
Clinic A:  "Patient Name"  |  "Appt Date"     |  "Pick-up Address"
Clinic B:  "Full Name"     |  "Service Date"   |  "Origin"
Clinic C:  "Passenger"     |  "Date/Time"      |  "From Address"
```

Manually mapping each format is slow and error-prone. This parser eliminates that entirely.

## What the AI Does

Upload any clinic Excel file. The AI reads the headers, examines sample rows, and figures out which columns map to which fields — in a single API call. No templates, no configuration, no manual mapping.

**Input** — a messy Excel file with inconsistent columns:

| Paciente | Telefono | Cita | Direccion de recogida | W/C? | Destino |
|----------|----------|------|-----------------------|------|---------|
| Juan G. | (305) 555-0011 | 12/5/25 8:10am | 1230 NW 5th St Apt 4B Miami 33125 | Yes | Jackson 1611 12th |

**Output** — clean, standardized JSON with GPS coordinates:

```json
{
  "passenger_name": "Juan G.",
  "country_code": "+1",
  "passenger_phone": "3055550011",
  "passenger_language": "es",
  "service_type_id": 7,
  "source": "1230 NW 5th Street, Apartment 4B, Miami, FL 33125",
  "pickup_latitude": 25.7780827,
  "pickup_longitude": -80.2154498,
  "destination": "Jackson Cancer Center, 1611 NW 12th Avenue, Miami, FL 33136",
  "dropoff_latitude": 25.7957767,
  "dropoff_longitude": -80.2152613,
  "pickup_date_time": "2025-12-05 08:10:00",
  "appointment_time": "2025-12-05 09:00:00",
  "special_note": null,
  "return_trip_needed": "yes",
  "return_trip_type": "immediate"
}
```

Notice what the AI did automatically:
- Mapped Spanish column headers (`Paciente`, `Telefono`, `Cita`) to standard fields
- Stripped phone formatting to digits only
- Detected language as Spanish from context
- Parsed `12/5/25 8:10am` into `2025-12-05 08:10:00`
- Detected `W/C? = Yes` as wheelchair (service_type_id `7`)
- Expanded `Jackson 1611 12th` to the full clinic name and address
- Added GPS coordinates for both pickup and dropoff

---

## AI-Powered Features

### 1. Smart Column Detection
Claude AI analyzes column headers and sample data to automatically map any Excel layout to the standardized schema. Handles English, Spanish, abbreviations, and nonstandard naming. One LLM call per file — not per row — so a 1,000-row file processes in the same time as a 10-row file.

### 2. Address Standardization
Abbreviated or partial addresses are expanded to full standardized form. The AI resolves clinic shorthand, adds missing city/state/zip, and corrects formatting:
- `Jackson 1611 12th` becomes `Jackson Cancer Center, 1611 NW 12th Avenue, Miami, FL 33136`
- `1230 NW 5th St Apt 4B Miami 33125` becomes `1230 NW 5th Street, Apartment 4B, Miami, FL 33125`

### 3. Service Type Inference
Detects wheelchair, stretcher, and ambulatory needs from any format — dedicated columns, free-text notes, or abbreviations:
- `"Wheelchair"`, `"W/C"`, `"WC"`, `"Yes"` in a wheelchair column → service_type_id `7`
- `"Stretcher"`, `"Gurney"`, `"Strech"` → service_type_id `9`
- Everything else defaults to ambulatory (`1`)

### 4. Multi-Format Date/Time Parsing
Handles real-world date and time formats without configuration:
- Dates: `12/05/2025`, `2025-12-05`, `05-Dec-2025`, `12/5/25`
- Times: `9:00 AM`, `09:00`, `9am`, `13:30:00`
- Combined: `12/5/25 8:10am` splits into date and time automatically

### 5. Phone Number Normalization
Any phone format in, clean 10-digit string out:
- `(305) 555-0011` → `3055550011`
- `305-555-0011` → `3055550011`
- `+1 (305) 555-0011` → `3055550011`

### 6. Language Detection
Identifies patient language preference from data context (Spanish names, Spanish column headers) and outputs standardized codes (`en`, `es`).

### 7. Return Trip Logic
Infers return trip needs and scheduling from free-text fields:
- `"Round Trip"` → `return_trip_needed: "yes"`, `return_trip_type: "immediate"`
- `"One Way"` → `return_trip_needed: "no"`
- `"Call when done"`, `"Wait"` → `return_trip_type: "immediate"`

### 8. GPS Geocoding
Converts every pickup and dropoff address to latitude/longitude coordinates using Google Maps (high accuracy) or OpenStreetMap (free). Coordinates enable routing, mapping, and ETA calculations downstream.

---

## Live API

**Endpoint:** `https://web-production-c09c8.up.railway.app`

Deployed on Railway with auto-deploy from `main` branch.

---

## Quick Start

```bash
curl -X POST https://web-production-c09c8.up.railway.app/api/upload \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -F "file=@your_clinic_file.xlsx" \
  -F "clinic_id=test_clinic" \
  -F "use_geocoding=true" \
  -F "use_llm=true"
```

---

## Processing Pipeline

```
Excel Upload
    |
    v
[1. Smart Column Detection] -- Claude AI maps columns to schema (1 API call)
    |
    v
[2. Data Extraction] -- pandas applies mapping to all rows instantly
    |
    v
[3. AI Normalization] -- addresses, dates, phones, service types, language
    |
    v
[4. GPS Geocoding] -- Google Maps or OpenStreetMap (optional)
    |
    v
Standardized JSON Response
```

The key architectural insight: the LLM is called **once** to understand the file structure, then fast deterministic code processes every row. This means a 1,800-row file takes ~10 seconds, not 30-60 minutes.

---

## Response Format

### Field Reference

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

## Performance

| Mode | Time | Cost per Trip | GPS | Clean Addresses |
|------|------|---------------|-----|-----------------|
| Basic parsing | ~0.02s | $0 | No | No |
| + Geocoding | ~1s | ~$0 (free tier) | Yes | No |
| + LLM + Geocoding | ~5-6s | ~$0.00025 | Yes | Yes |

**Monthly estimate (1,000 trips):** Google Maps $0 (within free tier), Claude ~$0.25. Total under $1/month.

---

## Configuration

Set these environment variables (see `.env.example`):

| Variable | Required | Description |
|----------|----------|-------------|
| `API_KEY` | Yes | Authentication key for API requests |
| `ANTHROPIC_API_KEY` | No | Enables AI-powered parsing via Claude |
| `GOOGLE_MAPS_API_KEY` | No | Enables Google Maps geocoding |
| `USE_LLM` | No | Default LLM setting (`true`/`false`, default: `false`) |
| `USE_GEOCODING` | No | Default geocoding setting (`true`/`false`, default: `false`) |
| `GEOCODING_PROVIDER` | No | `google` or `osm` (default: `google`) |

---

## Documentation

| Document | Audience | Purpose |
|----------|----------|---------|
| [API_DOCUMENTATION.md](API_DOCUMENTATION.md) | Developers | Full endpoint reference with schemas and examples |
| [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) | Website team | Code examples for Python, Node.js, PHP integration |
| [GETTING_STARTED.md](GETTING_STARTED.md) | New developers | Local setup and first-run instructions |
| [YOUR_JSON_FORMAT.md](YOUR_JSON_FORMAT.md) | Backend team | Detailed field mapping from Excel to JSON |
| [TEAM_HANDOFF.md](TEAM_HANDOFF.md) | Operations | Deployment, configuration, and handoff reference |
| [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) | DevOps | Railway-specific deployment guide |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Stakeholders | Architecture overview and project scope |

---

## License

MIT License. See [LICENSE](LICENSE).
