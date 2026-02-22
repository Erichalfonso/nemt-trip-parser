"""
NEMT Trip Parser - Production API Server

This is the main API server that your website team will connect to.
Accepts Excel uploads and returns standardized JSON trip data.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import time
from datetime import datetime
from werkzeug.utils import secure_filename
import traceback

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import our parser components
from nemt_parser.parsers import parse_messy_excel, enhance_with_claude, parse_excel_with_smart_llm
from nemt_parser.geocoding import geocode_trips_google, geocode_trips_free

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Configuration
UPLOAD_FOLDER = 'temp_uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# API Configuration (from environment variables)
API_KEY = os.getenv('API_KEY') or os.getenv('PARSER_API_KEY')
if not API_KEY:
    raise RuntimeError("API_KEY environment variable is required")
GOOGLE_MAPS_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
ANTHROPIC_KEY = os.getenv('ANTHROPIC_API_KEY')
USE_LLM = os.getenv('USE_LLM', 'false').lower() == 'true'
USE_GEOCODING = os.getenv('USE_GEOCODING', 'true').lower() == 'true'
GEOCODING_PROVIDER = os.getenv('GEOCODING_PROVIDER', 'google')


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def verify_api_key(request):
    """Verify API key from request headers"""
    provided_key = request.headers.get('X-API-Key')
    if not provided_key:
        return False, "Missing X-API-Key header"

    if provided_key != API_KEY:
        return False, "Invalid API key"

    return True, "OK"


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'features': {
            'llm_enhancement': ANTHROPIC_KEY is not None,
            'google_geocoding': GOOGLE_MAPS_KEY is not None,
            'free_geocoding': True
        }
    }), 200


@app.route('/api/upload', methods=['POST'])
def upload_trip_data():
    """
    Main endpoint: Upload Excel file and get standardized JSON

    Headers:
        X-API-Key: Authentication key

    Form Data:
        file: Excel file (.xlsx or .xls)
        clinic_id: Clinic identifier (optional)
        use_llm: Enable LLM enhancement (true/false, optional)
        use_geocoding: Enable geocoding (true/false, optional)

    Returns:
        JSON with standardized trip data
    """

    start_time = time.time()

    # Verify API key
    valid, message = verify_api_key(request)
    if not valid:
        return jsonify({
            'success': False,
            'error': message
        }), 401

    # Check if file was uploaded
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No file uploaded. Include file in multipart/form-data as "file"'
        }), 400

    file = request.files['file']

    # Check if filename is empty
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'Empty filename'
        }), 400

    # Check file extension
    if not allowed_file(file.filename):
        return jsonify({
            'success': False,
            'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400

    # Get optional parameters
    clinic_id = request.form.get('clinic_id', 'unknown')
    use_llm_param = request.form.get('use_llm', str(USE_LLM)).lower() == 'true'
    use_geocoding_param = request.form.get('use_geocoding', str(USE_GEOCODING)).lower() == 'true'

    try:
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_filename = f"{clinic_id}_{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        file.save(filepath)

        print(f"\n{'='*80}")
        print(f"Processing upload from clinic: {clinic_id}")
        print(f"File: {filename}")
        print(f"{'='*80}\n")

        # STEP 1 & 2: Parse Excel file (with optional LLM intelligence)
        if use_llm_param and ANTHROPIC_KEY:
            print("Step 1: Smart LLM Parsing (intelligent field extraction)...")
            trips = parse_excel_with_smart_llm(filepath, anthropic_api_key=ANTHROPIC_KEY)
            print(f"[OK] Parsed {len(trips)} trips with LLM intelligence\n")
        else:
            print("Step 1: Basic parsing (hardcoded column mapping)...")
            trips = parse_messy_excel(filepath)
            print(f"[OK] Parsed {len(trips)} trips\n")
            print("Note: Enable LLM for intelligent parsing of any Excel format\n")

        # STEP 2: Geocoding (optional)
        if use_geocoding_param:
            print("Step 2: Geocoding addresses...")

            # Save to temp JSON file for geocoding
            temp_json = filepath.replace('.xlsx', '.json').replace('.xls', '.json')
            with open(temp_json, 'w') as f:
                json.dump(trips, f)

            # Geocode based on provider
            if GEOCODING_PROVIDER == 'google' and GOOGLE_MAPS_KEY:
                print("Using Google Maps...")
                output_json = temp_json.replace('.json', '_geocoded.json')
                geocode_trips_google(
                    input_file=temp_json,
                    output_file=output_json,
                    api_key=GOOGLE_MAPS_KEY
                )
                with open(output_json, 'r') as f:
                    trips = json.load(f)
                os.remove(output_json)
            else:
                print("Using OpenStreetMap (free)...")
                output_json = temp_json.replace('.json', '_geocoded.json')
                geocode_trips_free(
                    input_file=temp_json,
                    output_file=output_json
                )
                with open(output_json, 'r') as f:
                    trips = json.load(f)
                os.remove(output_json)

            os.remove(temp_json)
            print(f"[OK] Geocoded {len(trips)} trips\n")
        else:
            print("Step 2: Skipping geocoding\n")

        # Clean up uploaded file
        os.remove(filepath)

        # Calculate processing time
        processing_time = time.time() - start_time

        print(f"{'='*80}")
        print(f"SUCCESS! Processed {len(trips)} trips in {processing_time:.2f} seconds")
        print(f"{'='*80}\n")

        # Return success response
        return jsonify({
            'success': True,
            'trips': trips,
            'total_trips': len(trips),
            'processing_time_seconds': round(processing_time, 2),
            'features_used': {
                'llm_enhancement': use_llm_param and ANTHROPIC_KEY is not None,
                'geocoding': use_geocoding_param,
                'geocoding_provider': GEOCODING_PROVIDER if use_geocoding_param else None
            }
        }), 200

    except Exception as e:
        # Log error
        print(f"\n{'='*80}")
        print(f"ERROR processing upload")
        print(f"{'='*80}")
        print(traceback.format_exc())
        print(f"{'='*80}\n")

        # Clean up files if they exist
        if os.path.exists(filepath):
            os.remove(filepath)

        # Return error response
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get API configuration and status"""

    # Verify API key
    valid, message = verify_api_key(request)
    if not valid:
        return jsonify({
            'success': False,
            'error': message
        }), 401

    return jsonify({
        'success': True,
        'configuration': {
            'llm_available': ANTHROPIC_KEY is not None,
            'llm_enabled_by_default': USE_LLM,
            'geocoding_enabled_by_default': USE_GEOCODING,
            'geocoding_provider': GEOCODING_PROVIDER,
            'google_maps_available': GOOGLE_MAPS_KEY is not None,
            'max_file_size_mb': MAX_FILE_SIZE / (1024 * 1024),
            'allowed_extensions': list(ALLOWED_EXTENSIONS)
        }
    }), 200


if __name__ == '__main__':
    # Get port from environment (Railway provides this)
    port = int(os.getenv('PORT', 5001))

    print("\n" + "="*80)
    print("NEMT TRIP PARSER API SERVER")
    print("="*80)
    print()
    print("Configuration:")
    print(f"  - LLM Enhancement: {'Enabled' if ANTHROPIC_KEY else 'Disabled (no API key)'}")
    print(f"  - Google Geocoding: {'Enabled' if GOOGLE_MAPS_KEY else 'Disabled (no API key)'}")
    print(f"  - Free Geocoding: Enabled")
    print(f"  - API Authentication: {'Enabled' if API_KEY else 'Disabled'}")
    print()
    print("Endpoints:")
    print("  - GET  /health       - Health check")
    print("  - POST /api/upload   - Upload Excel file")
    print("  - GET  /api/status   - Get configuration")
    print()
    print(f"Starting server on port {port}")
    print("="*80)
    print()

    # Run Flask development server
    app.run(host='0.0.0.0', port=port, debug=False)
