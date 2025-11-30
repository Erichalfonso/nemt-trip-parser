# NEMT Trip Parser

Intelligent Excel parser for NEMT (Non-Emergency Medical Transportation) trip data. Accepts messy clinic Excel files in any format and returns standardized JSON output.

## Features

- **Smart Column Mapping**: Automatically detects column names regardless of format
- **LLM Enhancement**: Uses Claude AI to clean and standardize addresses
- **Geocoding**: Converts addresses to GPS coordinates (Google Maps or OpenStreetMap)
- **Flexible Input**: Handles various date/time formats, phone number formats
- **RESTful API**: Simple HTTP endpoint for integration

## Quick Start

### Installation

```bash
# Clone repository
git clone <your-repo-url>
cd nemt-trip-parser

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your API keys
```

### Basic Usage

```python
from parse_messy_clinic import parse_messy_excel

# Parse Excel file
trips = parse_messy_excel()

# Output: Standardized JSON array
```

### API Usage

```bash
# Start the API server
python api_server.py

# Upload a file
curl -X POST http://localhost:5000/api/upload \
  -H "X-API-Key: your-api-key" \
  -F "file=@clinic_data.xlsx" \
  -F "clinic_id=clinic_123"
```

## Architecture

```
Excel Upload → Parser → LLM Enhancement → Geocoding → JSON Response
```

### Components

1. **Parser Layer** (`parse_messy_clinic.py`)
   - Extracts data from Excel files
   - Handles messy formats, dates, times

2. **Enhancement Layer** (`parse_with_llm.py`)
   - Claude AI integration
   - Cleans and standardizes addresses
   - Infers full clinic addresses from partial data

3. **Geocoding Layer** (`geocode_with_google.py`, `geocode_free.py`)
   - Google Maps API (accurate, paid)
   - OpenStreetMap (free, slower)

4. **API Layer** (`api_server.py`)
   - RESTful HTTP endpoint
   - Authentication via API key
   - Error handling and validation

## JSON Output Format

```json
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
  "appointment_time": "2025-12-05 11:15:00",
  "special_note": "Wheelchair accessible",
  "return_trip_needed": "yes",
  "return_trip_type": "immediate"
}
```

## Configuration

### Required Environment Variables

```bash
# API Keys
ANTHROPIC_API_KEY=your-claude-api-key
GOOGLE_MAPS_API_KEY=your-google-maps-key

# API Server
PARSER_API_KEY=your-secret-key-for-authentication
```

### Optional Configuration

- `use_llm`: Enable LLM enhancement (default: false)
- `use_geocoding`: Enable geocoding (default: false)
- `geocoding_provider`: "google" or "osm" (default: "google")

## Development

### Project Structure

```
nemt-trip-parser/
├── nemt_parser/              # Core library
│   ├── core/                 # Business logic
│   │   ├── models.py         # Data models
│   │   ├── parser.py         # Excel parsing
│   │   ├── mapper.py         # Column mapping
│   │   └── output_schema.py  # JSON serialization
│   ├── database/             # Database layer (optional)
│   └── integrations/         # Flask adapter
├── parse_messy_clinic.py     # Standalone parser
├── parse_with_llm.py         # LLM enhancement
├── geocode_with_google.py    # Google Maps geocoding
├── geocode_free.py           # OpenStreetMap geocoding
├── api_server.py             # Production API
└── tests/                    # Test files
```

### Running Tests

```bash
python test_parser.py
```

## Deployment

### Option 1: Traditional Server

```bash
# Install dependencies
pip install -r requirements.txt

# Run with gunicorn (production)
gunicorn -w 4 -b 0.0.0.0:5000 api_server:app
```

### Option 2: Docker

```bash
docker build -t nemt-parser .
docker run -p 5000:5000 -e ANTHROPIC_API_KEY=xxx nemt-parser
```

### Option 3: Cloud (AWS Lambda, etc.)

See `deployment/` directory for cloud-specific configurations.

## API Documentation

### POST /api/upload

Upload an Excel file for parsing.

**Headers:**
- `X-API-Key`: Authentication key

**Body (multipart/form-data):**
- `file`: Excel file (.xlsx or .xls)
- `clinic_id`: Clinic identifier
- `use_llm` (optional): Enable AI enhancement
- `use_geocoding` (optional): Add GPS coordinates

**Response:**
```json
{
  "success": true,
  "trips": [...],
  "total_trips": 10,
  "processing_time_seconds": 3.2
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-11-29T12:00:00Z"
}
```

## Cost Estimation

- **Claude API**: ~$0.00025 per trip (Haiku model)
- **Google Maps Geocoding**: $0.005 per address
- **Total per trip**: ~$0.01 (with both features enabled)
- **Monthly (1000 trips)**: ~$10

Google provides $200/month free credit, so most usage is free.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License

## Support

For issues or questions, contact: [your-email@company.com]

