"""
Data validation and transformation logic.

Handles converting raw Excel data into validated Trip objects,
with robust error handling and data cleaning.
"""

from datetime import datetime, date, time
from typing import Any, Optional
import re
from pydantic import ValidationError

from .models import Trip, TripType, ColumnMapping


class DataValidator:
    """
    Validates and transforms raw Excel data into Trip objects.

    Handles various data formats, date parsing, boolean conversion,
    and provides detailed error messages for troubleshooting.
    """

    @staticmethod
    def parse_date(value: Any) -> Optional[date]:
        """
        Parse various date formats into a date object.

        Handles:
        - datetime objects
        - date objects
        - Strings in formats: YYYY-MM-DD, MM/DD/YYYY, M/D/YY
        - Excel serial dates
        """
        if value is None or value == "":
            return None

        # Already a date object
        if isinstance(value, date):
            return value

        # datetime object
        if isinstance(value, datetime):
            return value.date()

        # Try parsing string formats
        if isinstance(value, str):
            value = value.strip()

            # Try common formats
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%Y%m%d", "%m-%d-%Y"]:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue

        # Try as numeric (Excel serial date)
        try:
            excel_date = float(value)
            # Excel dates start from 1900-01-01
            return datetime(1899, 12, 30) + datetime.timedelta(days=excel_date)
        except (ValueError, TypeError):
            pass

        return None

    @staticmethod
    def parse_time(value: Any) -> Optional[time]:
        """
        Parse various time formats into a time object.

        Handles:
        - time objects
        - datetime objects
        - Strings in formats: HH:MM, HH:MM:SS, H:MM AM/PM
        """
        if value is None or value == "":
            return None

        # Already a time object
        if isinstance(value, time):
            return value

        # datetime object
        if isinstance(value, datetime):
            return value.time()

        # Try parsing string formats
        if isinstance(value, str):
            value = value.strip()

            # Try common formats
            for fmt in ["%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M%p"]:
                try:
                    return datetime.strptime(value, fmt).time()
                except ValueError:
                    continue

        return None

    @staticmethod
    def parse_boolean(value: Any) -> bool:
        """
        Parse various boolean representations.

        Handles:
        - Python bools
        - Strings: yes/no, y/n, true/false, 1/0
        - Numbers: 1=True, 0=False
        """
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            value = value.strip().lower()
            if value in ("yes", "y", "true", "1", "x"):
                return True
            if value in ("no", "n", "false", "0", ""):
                return False

        if isinstance(value, (int, float)):
            return bool(value)

        return False

    @staticmethod
    def parse_trip_type(value: Any) -> TripType:
        """Parse trip type from various formats"""
        if isinstance(value, TripType):
            return value

        if isinstance(value, str):
            value = value.strip().lower()
            if "round" in value or "both" in value:
                return TripType.ROUND_TRIP
            elif "return" in value or "drop" in value:
                return TripType.RETURN
            elif "pickup" in value or "pick" in value:
                return TripType.PICKUP

        return TripType.ROUND_TRIP  # Default

    @staticmethod
    def clean_phone(value: Any) -> Optional[str]:
        """Clean and format phone numbers"""
        if value is None:
            return None

        phone = str(value).strip()
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)

        if len(digits) == 0:
            return None

        # Format as (XXX) XXX-XXXX if 10 digits
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"

        return phone  # Return as-is if not standard format

    @staticmethod
    def clean_zip(value: Any) -> str:
        """Clean and format ZIP codes"""
        if value is None:
            return ""

        zip_code = str(value).strip()
        # Remove non-alphanumeric
        zip_code = re.sub(r'[^0-9-]', '', zip_code)

        # Handle ZIP+4
        if '-' in zip_code:
            parts = zip_code.split('-')
            if len(parts[0]) == 5 and len(parts[1]) == 4:
                return zip_code

        # Ensure 5 digits for standard ZIP
        if len(zip_code) == 5:
            return zip_code

        # Pad with zeros if needed
        return zip_code.zfill(5) if zip_code.isdigit() else zip_code

    @classmethod
    def row_to_trip(
        cls,
        row_data: dict[str, Any],
        mapping: ColumnMapping,
        source_clinic_id: Optional[str] = None
    ) -> tuple[Optional[Trip], list[str]]:
        """
        Convert a raw Excel row into a validated Trip object.

        Args:
            row_data: Dictionary of column_name -> value from Excel
            mapping: ColumnMapping that defines the field transformation
            source_clinic_id: ID of the clinic (for tracking)

        Returns:
            Tuple of (Trip object or None, list of error messages)
        """
        errors = []

        try:
            # Build the trip data dictionary
            trip_data = {}

            # Helper function to get mapped value
            def get_value(field_name: str) -> Any:
                mapped_col = getattr(mapping, field_name, None)
                if mapped_col and mapped_col in row_data:
                    return row_data[mapped_col]
                return None

            # Parse each field with appropriate converter
            trip_data["patient_name"] = get_value("patient_name")
            trip_data["medicaid_id"] = get_value("medicaid_id")

            # Optional string fields
            trip_data["patient_phone"] = cls.clean_phone(get_value("patient_phone"))
            trip_data["pickup_address"] = get_value("pickup_address")
            trip_data["pickup_city"] = get_value("pickup_city")
            trip_data["pickup_state"] = get_value("pickup_state") or "FL"
            trip_data["pickup_zip"] = cls.clean_zip(get_value("pickup_zip"))

            trip_data["dropoff_address"] = get_value("dropoff_address")
            trip_data["dropoff_city"] = get_value("dropoff_city")
            trip_data["dropoff_state"] = get_value("dropoff_state") or "FL"
            trip_data["dropoff_zip"] = cls.clean_zip(get_value("dropoff_zip"))

            # Dates and times
            trip_data["appointment_date"] = cls.parse_date(get_value("appointment_date"))
            trip_data["appointment_time"] = cls.parse_time(get_value("appointment_time"))
            trip_data["date_of_birth"] = cls.parse_date(get_value("date_of_birth"))

            # Booleans
            wheelchair_val = get_value("wheelchair")
            trip_data["wheelchair"] = cls.parse_boolean(wheelchair_val) if wheelchair_val is not None else False

            stretcher_val = get_value("stretcher")
            trip_data["stretcher"] = cls.parse_boolean(stretcher_val) if stretcher_val is not None else False

            ambulatory_val = get_value("ambulatory")
            trip_data["ambulatory"] = cls.parse_boolean(ambulatory_val) if ambulatory_val is not None else True

            # Trip type
            trip_type_val = get_value("trip_type")
            if trip_type_val:
                trip_data["trip_type"] = cls.parse_trip_type(trip_type_val)

            # Additional fields
            trip_data["notes"] = get_value("notes")
            trip_data["appointment_type"] = get_value("appointment_type")
            trip_data["clinic_name"] = get_value("clinic_name")

            # Metadata
            trip_data["source_clinic_id"] = source_clinic_id or mapping.clinic_id
            trip_data["uploaded_at"] = datetime.now()

            # Create and validate Trip object
            trip = Trip(**trip_data)
            return trip, []

        except ValidationError as e:
            errors = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
            return None, errors
        except Exception as e:
            return None, [f"Unexpected error: {str(e)}"]
