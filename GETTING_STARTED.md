# NEMT Trip Parser - Getting Started

## 🎉 Your NEMT Trip Data Parser is Ready!

This tool solves your problem of receiving Excel files from multiple clinics with different column formats. It intelligently maps their columns to your standardized format.

---

## 📁 What Was Built

### Core Components

1. **Intelligent Column Mapper** (`nemt_parser/core/mapper.py`)
   - Auto-detects column names from Excel files
   - Suggests mappings using fuzzy matching
   - Handles variations like "Patient Name" vs "Full Name" vs "Client"

2. **Excel Parser** (`nemt_parser/core/parser.py`)
   - Reads Excel files (`.xlsx`, `.xls`)
   - Applies saved column mappings
   - Validates and transforms data

3. **Data Validator** (`nemt_parser/core/validator.py`)
   - Converts various date formats
   - Cleans phone numbers and ZIP codes
   - Handles boolean fields (Yes/No, Y/N, 1/0, etc.)

4. **Database Layer** (`nemt_parser/database/`)
   - Stores clinic mappings (one-time setup per clinic)
   - Saves parsed trip data
   - Tracks upload history

5. **Flask API Integration** (`nemt_parser/integrations/flask_adapter.py`)
   - RESTful API endpoints
   - Receives Excel via HTTP
   - Returns standardized JSON

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd C:\Users\erich\nemt-trip-parser
pip install -r requirements.txt
```

### 2. Test with Sample Data

```bash
python test_parser.py
```

This will:
- Create sample Excel files from 3 different "clinics"
- Test the parser with different column formats
- Show you the standardized JSON output
- Save data to `test_nemt_trips.db`

### 3. Start the API Server

```bash
python -m nemt_parser.integrations.flask_adapter
```

The API will run at `http://localhost:5000`

### 4. Test the API

```bash
# Upload an Excel file
curl -X POST http://localhost:5000/api/nemt/upload \
  -F "file=@sample_data/clinic_a_trips.xlsx" \
  -F "clinic_id=miami_medical"
```

---

## 🔄 How It Works

### First-Time Clinic Upload

```
1. Clinic uploads Excel file → Your API
2. Parser detects columns: ["Patient Name", "Medicaid #", ...]
3. AI suggests mapping:
   {
     "patient_name": "Patient Name",
     "medicaid_id": "Medicaid #",
     ...
   }
4. You (or clinic) review and confirm mapping
5. Mapping saved to database
```

### Subsequent Uploads

```
1. Clinic uploads Excel file → Your API
2. Parser loads saved mapping automatically
3. Data parsed and returned as standardized JSON
4. No manual mapping needed! ✨
```

---

## 📊 Standardized JSON Output

No matter what format clinics send, you always get this:

```json
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
  "notes": "Patient needs assistance walking"
}
```

---

## 🔌 Integration with Your Website

You have **3 options**:

### Option 1: Use the Flask API (Recommended)

Run the parser as a microservice:

```bash
python -m nemt_parser.integrations.flask_adapter
```

Your existing website calls it:

```javascript
// From your website's JavaScript
const formData = new FormData();
formData.append('file', excelFile);
formData.append('clinic_id', 'miami_medical');

const response = await fetch('http://localhost:5000/api/nemt/upload', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log(result.trips); // Standardized trip data!
```

### Option 2: Direct Python Integration

Import directly into your Python backend:

```python
from nemt_parser import TripParser, MappingRepository

# In your existing upload handler
def handle_clinic_upload(excel_file_path, clinic_id):
    repo = MappingRepository("postgresql://user:pass@localhost/mydb")
    parser = TripParser(mapping_repository=repo)

    result = parser.parse_excel(excel_file_path, clinic_id=clinic_id)

    return {
        "trips": [trip.model_dump() for trip in result.trips],
        "success": result.success
    }
```

### Option 3: Copy the Code

The parser is modular - copy just what you need:
- `nemt_parser/core/` - Core parsing logic
- `nemt_parser/database/` - Database schemas
- Adapt to your existing architecture

---

## 📖 API Endpoints

See **`API_DOCUMENTATION.md`** for complete API reference.

**Main endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/nemt/upload` | Upload Excel file, get JSON trips |
| `POST` | `/api/nemt/mapping/save` | Save/update clinic mapping |
| `GET` | `/api/nemt/mapping/<clinic_id>` | Get saved mapping |
| `GET` | `/api/nemt/clinics` | List all clinics |
| `GET` | `/api/nemt/history` | Upload history |

---

## 🗂️ Project Structure

```
nemt-trip-parser/
├── nemt_parser/                   # Main package
│   ├── core/                      # Core parsing logic
│   │   ├── parser.py             # Main Excel parser
│   │   ├── mapper.py             # Column mapping intelligence
│   │   ├── validator.py          # Data validation & cleaning
│   │   └── models.py             # Data models (Pydantic)
│   ├── database/                  # Database layer
│   │   ├── repositories.py       # Data access
│   │   └── schemas.py            # SQLAlchemy models
│   └── integrations/              # Framework integrations
│       └── flask_adapter.py      # Flask API
│
├── examples/                      # Usage examples
│   ├── basic_usage.py            # Python examples
│   └── create_sample_data.py     # Generate test files
│
├── sample_data/                   # Sample Excel files
│   ├── clinic_a_trips.xlsx       # Miami Medical format
│   ├── clinic_b_trips.xlsx       # Orlando Clinic format
│   └── clinic_c_trips.xlsx       # Tampa General format
│
├── tests/                         # Unit tests (TODO)
├── test_parser.py                # Integration test
├── requirements.txt              # Dependencies
├── README.md                     # Project overview
├── API_DOCUMENTATION.md          # API reference
└── GETTING_STARTED.md            # This file
```

---

## 🛠️ Configuration

### Database

By default uses SQLite (`sqlite:///nemt_trips.db`)

For production, use PostgreSQL:

```python
# In your code or Flask config
database_url = "postgresql://user:password@localhost:5432/nemt_production"

repo = MappingRepository(database_url)
parser = TripParser(mapping_repository=repo)
```

### Supported Databases

- SQLite: `sqlite:///nemt_trips.db`
- PostgreSQL: `postgresql://user:pass@host/dbname`
- MySQL: `mysql://user:pass@host/dbname`

---

## 🧪 Testing

### Run the Test Suite

```bash
python test_parser.py
```

### Test Individual Clinics

```python
from nemt_parser import TripParser, MappingRepository

repo = MappingRepository()
parser = TripParser(mapping_repository=repo)

result = parser.parse_excel(
    file_path="path/to/clinic_file.xlsx",
    clinic_id="test_clinic"
)

print(f"Parsed {result.successful_rows} trips")
for trip in result.trips:
    print(trip.model_dump())
```

---

## 📋 Next Steps

### Immediate

1. ✅ **Test with your real clinic data**
   - Place a real Excel file in `sample_data/`
   - Run `python test_parser.py` with your file
   - Review the suggested mapping
   - Adjust if needed

2. ✅ **Integrate with your website**
   - Choose integration method (API or direct)
   - Add upload endpoint to your backend
   - Test with postman or cURL

3. ✅ **Set up production database**
   - Configure PostgreSQL
   - Update connection string
   - Run database migrations if needed

### Future Enhancements

1. **Add LLM-powered mapping** (optional)
   - Use Claude/GPT to suggest mappings
   - Better accuracy for unusual column names
   - See `nemt_parser/llm/` (TODO)

2. **Build UI for mapping review**
   - Frontend to review/edit mappings
   - Drag-and-drop column matching
   - Save approved mappings

3. **Add more validation rules**
   - Custom validators for your business logic
   - Address validation (Google Maps API?)
   - Medicaid ID format checking

4. **Monitoring & Analytics**
   - Track parsing success rates
   - Alert on high failure rates
   - Clinic upload frequency

---

## 🆘 Troubleshooting

### Import Errors

```bash
ModuleNotFoundError: No module named 'pydantic'
```

**Solution:**
```bash
pip install -r requirements.txt
```

### Excel File Not Found

```
ERROR: Sample file not found: sample_data/clinic_a_trips.xlsx
```

**Solution:**
```bash
python examples/create_sample_data.py
```

### Database Locked (SQLite)

```
sqlite3.OperationalError: database is locked
```

**Solution:**
- Close other database connections
- Or switch to PostgreSQL for multi-user access

### Mapping Issues

If the auto-suggested mapping is wrong:

1. Review the suggested mapping in the API response
2. Edit the mapping JSON
3. POST corrected mapping to `/api/nemt/mapping/save`
4. Future uploads will use corrected mapping

---

## 📞 Support

- **Documentation**: See `README.md` and `API_DOCUMENTATION.md`
- **Examples**: Check `/examples` directory
- **Test Files**: Use sample data in `/sample_data`

---

## 🎯 Summary

You now have a complete NEMT trip data parser that:

- ✅ **Accepts Excel uploads** from multiple clinics
- ✅ **Intelligently maps columns** with AI-assistance
- ✅ **Returns standardized JSON** every time
- ✅ **Saves mappings** for future use
- ✅ **Provides a REST API** for easy integration
- ✅ **Handles various date/time formats** automatically
- ✅ **Validates and cleans data** (phone numbers, ZIP codes, etc.)
- ✅ **Tracks upload history** for auditing

**Ready to integrate into your existing website!** 🚀
