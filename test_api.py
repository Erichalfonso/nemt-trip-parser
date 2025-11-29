"""
Test the API server with a real file upload
"""

import requests
import json

# Configuration
API_URL = "http://localhost:5001/api/upload"
API_KEY = "REDACTED_API_KEY"
EXCEL_FILE = r"C:\Users\erich\Downloads\ppol_example_small_clinic_messy.xlsx"

# Prepare the request
headers = {
    'X-API-Key': API_KEY
}

files = {
    'file': open(EXCEL_FILE, 'rb')
}

data = {
    'clinic_id': 'test_clinic',
    'use_geocoding': 'true',
    'use_llm': 'false'  # Set to 'true' if you want LLM enhancement
}

print("="*80)
print("TESTING API UPLOAD")
print("="*80)
print(f"URL: {API_URL}")
print(f"File: {EXCEL_FILE}")
print()
print("Sending request...")
print()

# Make the request
response = requests.post(API_URL, headers=headers, files=files, data=data)

# Print response
print("="*80)
print(f"STATUS: {response.status_code}")
print("="*80)
print()

if response.status_code == 200:
    result = response.json()
    print(f"Success: {result['success']}")
    print(f"Total trips: {result['total_trips']}")
    print(f"Processing time: {result['processing_time_seconds']}s")
    print()
    print("="*80)
    print("FIRST TRIP (Sample):")
    print("="*80)
    print(json.dumps(result['trips'][0], indent=2))
else:
    print("ERROR:")
    print(response.text)
