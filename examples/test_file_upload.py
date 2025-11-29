"""
Test: How to Send Excel Files Through API

This demonstrates different ways to upload Excel files to the parser API.
"""

import requests
from pathlib import Path


def example_1_simple_upload():
    """
    Simplest way to upload an Excel file via API
    """
    print("=" * 70)
    print("Example 1: Simple File Upload")
    print("=" * 70)

    excel_file = Path("sample_data/clinic_a_trips.xlsx")

    if not excel_file.exists():
        print("ERROR: Run 'python examples/create_sample_data.py' first")
        return

    # Open the file
    with open(excel_file, 'rb') as f:
        # Send to API
        response = requests.post(
            'http://localhost:5000/api/nemt/upload',
            files={'file': f},  # ← This sends the Excel file!
            data={'clinic_id': 'test_clinic'}
        )

    # Get JSON response
    result = response.json()

    print(f"Status: {response.status_code}")
    print(f"Response: {result}")
    print()


def example_2_upload_with_filename():
    """
    Upload with custom filename
    """
    print("=" * 70)
    print("Example 2: Upload with Custom Filename")
    print("=" * 70)

    excel_file = Path("sample_data/clinic_a_trips.xlsx")

    # You can specify the filename
    files = {
        'file': ('my_custom_name.xlsx', open(excel_file, 'rb'))
    }

    response = requests.post(
        'http://localhost:5000/api/nemt/upload',
        files=files,
        data={'clinic_id': 'test_clinic_2'}
    )

    print(f"Status: {response.status_code}")
    print(f"Response keys: {response.json().keys()}")
    print()


def example_3_upload_from_memory():
    """
    Upload file from memory (not from disk)

    Useful if the Excel file is generated dynamically
    or received from another API.
    """
    print("=" * 70)
    print("Example 3: Upload from Memory")
    print("=" * 70)

    excel_file = Path("sample_data/clinic_a_trips.xlsx")

    # Read entire file into memory
    file_bytes = excel_file.read_bytes()

    # Send bytes directly
    files = {
        'file': ('trips.xlsx', file_bytes)
    }

    response = requests.post(
        'http://localhost:5000/api/nemt/upload',
        files=files,
        data={'clinic_id': 'test_clinic_3'}
    )

    print(f"Status: {response.status_code}")
    print(f"File size: {len(file_bytes)} bytes")
    print()


def example_4_what_gets_sent():
    """
    Show exactly what data is being sent
    """
    print("=" * 70)
    print("Example 4: What Gets Sent in the HTTP Request")
    print("=" * 70)

    excel_file = Path("sample_data/clinic_a_trips.xlsx")

    # Prepare the request
    files = {'file': open(excel_file, 'rb')}
    data = {'clinic_id': 'test_clinic_4', 'clinic_name': 'Test Clinic'}

    # Create a prepared request to inspect it
    req = requests.Request(
        'POST',
        'http://localhost:5000/api/nemt/upload',
        files=files,
        data=data
    )
    prepared = req.prepare()

    print(f"URL: {prepared.url}")
    print(f"Method: {prepared.method}")
    print(f"Headers: {dict(prepared.headers)}")
    print(f"Body preview: {str(prepared.body[:200])}...")
    print()


def example_5_simulating_browser_upload():
    """
    Simulate what happens when user uploads via browser
    """
    print("=" * 70)
    print("Example 5: Browser-Style Upload Simulation")
    print("=" * 70)

    # This is what happens behind the scenes when a user
    # selects a file in your website and clicks "Upload"

    excel_file = Path("sample_data/clinic_a_trips.xlsx")

    # Browser sends file with these headers
    files = {
        'file': (
            excel_file.name,  # filename
            open(excel_file, 'rb'),  # file content
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'  # MIME type
        )
    }

    response = requests.post(
        'http://localhost:5000/api/nemt/upload',
        files=files,
        data={'clinic_id': 'browser_upload'}
    )

    print(f"Status: {response.status_code}")
    result = response.json()

    if result.get('success'):
        print(f"✓ Successfully parsed {result['trips_parsed']} trips")
    elif result.get('needs_mapping'):
        print(f"✓ Detected {len(result['detected_columns'])} columns")
        print(f"  Columns: {', '.join(result['detected_columns'][:5])}...")

    print()


def example_6_check_file_size():
    """
    Check file size before uploading
    """
    print("=" * 70)
    print("Example 6: File Size Validation")
    print("=" * 70)

    excel_file = Path("sample_data/clinic_a_trips.xlsx")

    file_size = excel_file.stat().st_size
    max_size = 16 * 1024 * 1024  # 16MB

    print(f"File: {excel_file.name}")
    print(f"Size: {file_size:,} bytes ({file_size / 1024:.2f} KB)")
    print(f"Max allowed: {max_size:,} bytes ({max_size / 1024 / 1024:.0f} MB)")

    if file_size > max_size:
        print("❌ File too large!")
    else:
        print("✓ File size OK")

        # Upload it
        with open(excel_file, 'rb') as f:
            response = requests.post(
                'http://localhost:5000/api/nemt/upload',
                files={'file': f},
                data={'clinic_id': 'size_test'}
            )

        print(f"Upload status: {response.status_code}")

    print()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("FILE UPLOAD EXAMPLES")
    print("=" * 70)
    print()
    print("NOTE: Start the API first with:")
    print("  python -m nemt_parser.integrations.flask_adapter")
    print()
    input("Press Enter when API is running...")
    print()

    try:
        # Run examples
        example_1_simple_upload()
        example_2_upload_with_filename()
        example_3_upload_from_memory()
        example_4_what_gets_sent()
        example_5_simulating_browser_upload()
        example_6_check_file_size()

        print("=" * 70)
        print("✓ All examples completed!")
        print("=" * 70)

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to API")
        print("Make sure the API is running:")
        print("  python -m nemt_parser.integrations.flask_adapter")
