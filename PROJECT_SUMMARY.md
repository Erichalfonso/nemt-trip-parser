# Project Summary

Architecture overview and scope of the NEMT Trip Parser.

---

## What It Does

The NEMT Trip Parser accepts Excel files from clinics in any column format and returns standardized JSON trip data with optional GPS coordinates. It eliminates the need to manually process different clinic spreadsheet formats.

**Input:** Messy clinic Excel files with varying column names and formats.

**Output:** Consistent JSON with 17 standardized fields per trip.

---

## AI Capabilities

The parser uses Claude AI for intelligent processing:

- **Smart Column Detection:** LLM analyzes headers and sample data to map any Excel layout to the standard schema in a single API call.
- **Address Standardization:** Expands partial or abbreviated addresses to full form.
- **Service Type Inference:** Detects wheelchair/stretcher/ambulatory needs from free-text notes and abbreviations.
- **Multi-Format Parsing:** Handles diverse date, time, and phone number formats automatically.
- **Language Detection:** Identifies patient language preference from data context.
- **Return Trip Logic:** Infers return trip needs and scheduling from free-text fields.

---

## Architecture

```
Client (Website Backend)
    |
    v
Flask API Server (api_server.py)
    |
    +-- Smart LLM Parser (parse_smart_llm.py)
    |       Uses Claude to map columns, then pandas for extraction
    |
    +-- Rule-Based Parser (parse_messy_clinic.py)
    |       Fallback when LLM is disabled
    |
    +-- Geocoding Layer
    |       Google Maps (geocode_with_google.py)
    |       OpenStreetMap (geocode_free.py)
    |
    v
Standardized JSON Response
```

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/health` | No | Health check |
| `POST` | `/api/upload` | Yes | Upload Excel, get JSON trips |
| `GET` | `/api/status` | Yes | Server configuration |

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for full details.

---

## Core Components

| File | Purpose |
|------|---------|
| `api_server.py` | Flask API server with auth, upload handling, and response formatting |
| `parse_smart_llm.py` | AI-powered parser: LLM column mapping + pandas extraction |
| `parse_messy_clinic.py` | Rule-based parser for known formats |
| `parse_with_llm.py` | LLM enhancement utilities for address cleaning |
| `geocode_with_google.py` | Google Maps Geocoding API integration |
| `geocode_free.py` | OpenStreetMap/Nominatim geocoding |
| `nemt_parser/` | Core package with parsing logic, data models, and validation |

---

## Deployment

- **Platform:** Railway (auto-deploys from `main` branch)
- **Runtime:** Python 3.11 + Gunicorn
- **Build time:** ~2-3 minutes
- **Zero-downtime deployments**

See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for deployment details.

---

## Cost

| Service | Monthly Cost (1,000 trips) |
|---------|---------------------------|
| Google Maps Geocoding | $0 (within $200/month free tier) |
| Claude API (LLM parsing) | ~$0.25 |
| Railway hosting | $5 |
| **Total** | **~$5.25/month** |

---

## Documentation

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Main entry point and feature overview |
| [API_DOCUMENTATION.md](API_DOCUMENTATION.md) | Endpoint reference |
| [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) | Website integration code examples |
| [GETTING_STARTED.md](GETTING_STARTED.md) | Local setup instructions |
| [YOUR_JSON_FORMAT.md](YOUR_JSON_FORMAT.md) | Field mapping details |
| [TEAM_HANDOFF.md](TEAM_HANDOFF.md) | Operations handoff reference |
| [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) | Deployment guide |

---

Back to [README](README.md).
