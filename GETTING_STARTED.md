# Getting Started

Local setup and first-run instructions for the NEMT Trip Parser.

---

## Prerequisites

- Python 3.11+
- pip

---

## Installation

```bash
git clone https://github.com/Erichalfonso/nemt-trip-parser.git
cd nemt-trip-parser
pip install -r requirements.txt
```

---

## Configuration

Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```env
API_KEY=your-secure-api-key
ANTHROPIC_API_KEY=your-claude-key      # optional, enables LLM parsing
GOOGLE_MAPS_API_KEY=your-google-key    # optional, enables geocoding
USE_LLM=false
USE_GEOCODING=false
GEOCODING_PROVIDER=google
```

At minimum, `API_KEY` is required to start the server.

---

## Start the Server

**Development:**

```bash
python api_server.py
```

**Production:**

```bash
gunicorn -w 4 -b 0.0.0.0:5001 api_server:app
```

The server runs on `http://localhost:5001`.

---

## Test the API

### Health check

```bash
curl http://localhost:5001/health
```

### Upload a file

```bash
curl -X POST http://localhost:5001/api/upload \
  -H "X-API-Key: your-secure-api-key" \
  -F "file=@sample_data/clinic_a_trips.xlsx" \
  -F "clinic_id=test_clinic"
```

This returns standardized JSON with parsed trip data.

---

## Run Tests

```bash
python -m pytest tests/ -v
```

---

## Project Structure

```
nemt-trip-parser/
├── api_server.py              # Production API server (Flask)
├── parse_smart_llm.py         # AI-powered Excel parser
├── parse_messy_clinic.py      # Rule-based Excel parser
├── parse_with_llm.py          # LLM enhancement utilities
├── geocode_with_google.py     # Google Maps geocoding
├── geocode_free.py            # OpenStreetMap geocoding
├── nemt_parser/               # Core parser package
│   ├── core/                  # Parsing logic, models, validation
│   ├── database/              # Database schemas and repositories
│   └── integrations/          # Framework adapters
├── tests/                     # Test suite
├── sample_data/               # Sample Excel files for testing
├── examples/                  # Usage examples
└── docs (*.md)                # Documentation files
```

---

## How It Works

1. **Upload:** Client sends an Excel file via `POST /api/upload`
2. **Parse:** The parser detects columns and extracts trip data. With LLM enabled, Claude analyzes headers and sample rows to create an intelligent column mapping.
3. **Normalize:** Dates, times, phone numbers, addresses, and service types are standardized.
4. **Geocode (optional):** Addresses are converted to GPS coordinates.
5. **Respond:** Standardized JSON is returned to the client.

---

## Integration

See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for code examples in Python, Node.js, and PHP.

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for the full endpoint reference.

---

## Troubleshooting

**`ModuleNotFoundError`:** Run `pip install -r requirements.txt`.

**Server won't start:** Ensure `API_KEY` is set in your `.env` file. The server requires this variable.

**Geocoding returns null coordinates:** Verify `GOOGLE_MAPS_API_KEY` is set and the Geocoding API is enabled in Google Cloud Console.

**LLM parsing not working:** Verify `ANTHROPIC_API_KEY` is set and valid. Pass `use_llm=true` in the request.

---

Back to [README](README.md).
