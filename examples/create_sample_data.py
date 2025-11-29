"""
Generate sample Excel files for testing the NEMT parser.

This creates Excel files with different column naming conventions
to test the intelligent mapping feature.
"""

import pandas as pd
from datetime import date, time, timedelta
from pathlib import Path


def create_clinic_a_data():
    """
    Create sample data from "Clinic A" - Miami Medical Center.

    Uses one naming convention.
    """
    data = {
        "Patient Name": [
            "John Smith",
            "Maria Garcia",
            "Robert Johnson",
            "Lisa Chen",
            "David Williams"
        ],
        "Medicaid #": [
            "MCD123456789",
            "MCD987654321",
            "MCD555666777",
            "MCD111222333",
            "MCD999888777"
        ],
        "Patient Phone": [
            "305-123-4567",
            "305-234-5678",
            "305-345-6789",
            "305-456-7890",
            "305-567-8901"
        ],
        "Pick-up Address": [
            "123 Main St",
            "456 Oak Ave",
            "789 Pine Rd",
            "321 Elm St",
            "654 Maple Dr"
        ],
        "Pick-up City": [
            "Miami",
            "Miami",
            "Hialeah",
            "Coral Gables",
            "Miami Beach"
        ],
        "Pick-up ZIP": [
            "33101",
            "33102",
            "33012",
            "33134",
            "33139"
        ],
        "Drop-off Address": [
            "999 Hospital Blvd",
            "888 Medical Center Dr",
            "777 Clinic Way",
            "666 Doctor Ave",
            "555 Healthcare Pkwy"
        ],
        "Drop-off City": [
            "Miami",
            "Miami",
            "Miami",
            "Coral Gables",
            "Miami"
        ],
        "Drop-off ZIP": [
            "33125",
            "33126",
            "33127",
            "33134",
            "33128"
        ],
        "Appt Date": [
            "2025-01-15",
            "2025-01-15",
            "2025-01-16",
            "2025-01-16",
            "2025-01-17"
        ],
        "Appt Time": [
            "09:00 AM",
            "10:30 AM",
            "02:00 PM",
            "11:00 AM",
            "03:30 PM"
        ],
        "Wheelchair?": [
            "No",
            "Yes",
            "No",
            "No",
            "Yes"
        ],
        "Notes": [
            "Patient needs assistance walking",
            "Bring extra time",
            "",
            "Call upon arrival",
            "Service dog accompanies patient"
        ]
    }

    df = pd.DataFrame(data)
    return df


def create_clinic_b_data():
    """
    Create sample data from "Clinic B" - Orlando Clinic.

    Uses different column names to test mapping.
    """
    data = {
        "Full Name": [
            "Sarah Anderson",
            "Michael Brown",
            "Jennifer Taylor"
        ],
        "Insurance ID": [
            "MCD444555666",
            "MCD777888999",
            "MCD123789456"
        ],
        "Contact Number": [
            "(407) 123-4567",
            "(407) 234-5678",
            "(407) 345-6789"
        ],
        "Origin Address": [
            "100 Lake St",
            "200 Park Ave",
            "300 River Rd"
        ],
        "Origin City": [
            "Orlando",
            "Winter Park",
            "Orlando"
        ],
        "Origin ZIP": [
            "32801",
            "32789",
            "32802"
        ],
        "Destination Address": [
            "400 Hospital Way",
            "500 Medical Plaza",
            "600 Health Center"
        ],
        "Destination City": [
            "Orlando",
            "Orlando",
            "Kissimmee"
        ],
        "Destination ZIP": [
            "32803",
            "32804",
            "34741"
        ],
        "Service Date": [
            "01/20/2025",
            "01/21/2025",
            "01/22/2025"
        ],
        "Service Time": [
            "8:30",
            "14:00",
            "9:00"
        ],
        "WC Required": [
            "N",
            "Y",
            "N"
        ],
        "Special Instructions": [
            "Ring doorbell",
            "Apartment 4B",
            "Gate code: 1234"
        ]
    }

    df = pd.DataFrame(data)
    return df


def create_clinic_c_data():
    """
    Create sample data from "Clinic C" - Tampa General.

    Uses yet another naming convention.
    """
    data = {
        "Patient": [
            "William Davis",
            "Elizabeth Martinez",
            "James Wilson",
            "Mary Rodriguez"
        ],
        "Member ID": [
            "MCD321654987",
            "MCD147258369",
            "MCD963852741",
            "MCD789456123"
        ],
        "Phone": [
            "8135551234",
            "8135552345",
            "8135553456",
            "8135554567"
        ],
        "Pickup Location": [
            "700 Bay St, Tampa, FL 33601",
            "800 Harbor Dr, Tampa, FL 33602",
            "900 Shore Blvd, Tampa, FL 33603",
            "1000 Coast Ave, Tampa, FL 33604"
        ],
        "Dropoff Location": [
            "Tampa General Hospital, 1 Tampa General Cir, Tampa, FL 33606",
            "St Joseph's Hospital, 3001 W Dr Martin Luther King Jr Blvd, Tampa, FL 33607",
            "Memorial Hospital, 2901 Swann Ave, Tampa, FL 33609",
            "Tampa General Hospital, 1 Tampa General Cir, Tampa, FL 33606"
        ],
        "Appointment Date": [
            "1/25/2025",
            "1/26/2025",
            "1/27/2025",
            "1/28/2025"
        ],
        "Appointment Time": [
            "10:00 AM",
            "11:30 AM",
            "1:00 PM",
            "3:30 PM"
        ],
        "Mobility Aid": [
            "None",
            "Wheelchair",
            "Walker",
            "Wheelchair"
        ],
        "Comments": [
            "",
            "Needs extra assistance",
            "Bring walker from home",
            "Heavy patient"
        ]
    }

    df = pd.DataFrame(data)
    return df


def main():
    """Generate all sample files"""
    # Create sample_data directory
    output_dir = Path(__file__).parent.parent / "sample_data"
    output_dir.mkdir(exist_ok=True)

    print("Generating sample Excel files...")
    print(f"Output directory: {output_dir}\n")

    # Generate files
    files = [
        ("clinic_a_trips.xlsx", create_clinic_a_data(), "Miami Medical Center"),
        ("clinic_b_trips.xlsx", create_clinic_b_data(), "Orlando Clinic"),
        ("clinic_c_trips.xlsx", create_clinic_c_data(), "Tampa General Hospital"),
    ]

    for filename, df, clinic_name in files:
        file_path = output_dir / filename
        df.to_excel(file_path, index=False, engine='openpyxl')
        print(f"[OK] Created: {filename}")
        print(f"   Clinic: {clinic_name}")
        print(f"   Rows: {len(df)}")
        print(f"   Columns: {list(df.columns)[:3]}...\n")

    # Also create a second file for Clinic A to test returning clinic
    df_week2 = create_clinic_a_data()
    # Modify dates slightly
    for i, row in df_week2.iterrows():
        df_week2.at[i, 'Appt Date'] = "2025-01-22"

    file_path = output_dir / "clinic_a_trips_week2.xlsx"
    df_week2.to_excel(file_path, index=False, engine='openpyxl')
    print(f"[OK] Created: clinic_a_trips_week2.xlsx")
    print(f"   (Second upload from Clinic A for testing)\n")

    print("=" * 60)
    print("Sample files created successfully!")
    print(f"Location: {output_dir.absolute()}")
    print("\nYou can now test the parser with these files.")


if __name__ == "__main__":
    main()
