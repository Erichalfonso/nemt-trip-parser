"""
Test the live Railway API with a real Excel upload
"""

import requests
import json

# Your LIVE API URL
API_URL = "https://web-production-c09c8.up.railway.app/api/upload"
API_KEY = "nemt_parser_secret_key_2025"
EXCEL_FILE = r"C:\Users\erich\Downloads\ppol_example_small_clinic_messy.xlsx"

print("="*80)
print("TESTING LIVE RAILWAY API")
print("="*80)
print(f"URL: {API_URL}")
print(f"File: {EXCEL_FILE}")
print()
print("Uploading file to Railway...")
print()

# Prepare the request
headers = {'X-API-Key': API_KEY}
files = {'file': open(EXCEL_FILE, 'rb')}
data = {
    'clinic_id': 'test_clinic',
    'use_geocoding': 'true',
    'use_llm': 'false'
}

# Make the request
try:
    response = requests.post(API_URL, headers=headers, files=files, data=data, timeout=120)

    print("="*80)
    print(f"RESPONSE STATUS: {response.status_code}")
    print("="*80)
    print()

    if response.status_code == 200:
        result = response.json()

        print(f"✅ SUCCESS!")
        print(f"   Total trips parsed: {result['total_trips']}")
        print(f"   Processing time: {result['processing_time_seconds']}s")
        print()

        print("="*80)
        print("FIRST TRIP (Sample):")
        print("="*80)
        print(json.dumps(result['trips'][0], indent=2))
        print()

        print("="*80)
        print("FEATURES USED:")
        print("="*80)
        print(json.dumps(result['features_used'], indent=2))

    else:
        print(f"❌ ERROR: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"❌ EXCEPTION: {e}")
