"""
Intelligent column mapping logic.

Detects column names from Excel files and suggests mappings to
our standardized schema using fuzzy matching and keyword detection.
"""

from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher
import re

from .models import ColumnMapping


class ColumnMapper:
    """
    Intelligently maps clinic-specific column names to standardized fields.

    Uses fuzzy matching and keyword detection to suggest initial mappings,
    which can then be confirmed or adjusted before saving.
    """

    # Keyword patterns for each standardized field
    FIELD_PATTERNS = {
        "patient_name": [
            r"patient.*name",
            r"client.*name",
            r"name.*patient",
            r"full.*name",
            r"passenger.*name",
            r"^name$",
        ],
        "patient_phone": [
            r"phone",
            r"telephone",
            r"contact.*number",
            r"patient.*phone",
            r"cell",
            r"mobile",
        ],
        "medicaid_id": [
            r"medicaid.*id",
            r"medicaid.*#",
            r"medicaid.*number",
            r"insurance.*id",
            r"member.*id",
            r"policy.*number",
        ],
        "date_of_birth": [
            r"date.*birth",
            r"dob",
            r"birth.*date",
            r"patient.*dob",
        ],
        "pickup_address": [
            r"pick.*up.*address",
            r"pickup.*address",
            r"origin.*address",
            r"from.*address",
            r"start.*address",
        ],
        "pickup_city": [
            r"pick.*up.*city",
            r"pickup.*city",
            r"origin.*city",
            r"from.*city",
        ],
        "pickup_state": [
            r"pick.*up.*state",
            r"pickup.*state",
            r"origin.*state",
            r"from.*state",
        ],
        "pickup_zip": [
            r"pick.*up.*zip",
            r"pickup.*zip",
            r"origin.*zip",
            r"from.*zip",
        ],
        "dropoff_address": [
            r"drop.*off.*address",
            r"dropoff.*address",
            r"destination.*address",
            r"to.*address",
            r"appointment.*address",
        ],
        "dropoff_city": [
            r"drop.*off.*city",
            r"dropoff.*city",
            r"destination.*city",
            r"to.*city",
            r"appointment.*city",
        ],
        "dropoff_state": [
            r"drop.*off.*state",
            r"dropoff.*state",
            r"destination.*state",
            r"to.*state",
        ],
        "dropoff_zip": [
            r"drop.*off.*zip",
            r"dropoff.*zip",
            r"destination.*zip",
            r"to.*zip",
            r"appointment.*zip",
        ],
        "appointment_date": [
            r"appointment.*date",
            r"appt.*date",
            r"visit.*date",
            r"service.*date",
            r"trip.*date",
        ],
        "appointment_time": [
            r"appointment.*time",
            r"appt.*time",
            r"visit.*time",
            r"pickup.*time",
            r"scheduled.*time",
        ],
        "trip_type": [
            r"trip.*type",
            r"service.*type",
            r"direction",
        ],
        "wheelchair": [
            r"wheelchair",
            r"wc",
            r"needs.*wheelchair",
            r"mobility.*aid",
        ],
        "stretcher": [
            r"stretcher",
            r"gurney",
            r"ambulatory.*service",
        ],
        "ambulatory": [
            r"ambulatory",
            r"can.*walk",
            r"mobile",
        ],
        "notes": [
            r"notes",
            r"comments",
            r"special.*instructions",
            r"remarks",
        ],
        "appointment_type": [
            r"appointment.*type",
            r"appt.*type",
            r"visit.*type",
            r"procedure",
        ],
        "clinic_name": [
            r"clinic.*name",
            r"facility.*name",
            r"hospital.*name",
            r"provider.*name",
        ],
    }

    @classmethod
    def similarity_score(cls, str1: str, str2: str) -> float:
        """Calculate similarity between two strings (0.0 to 1.0)"""
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    @classmethod
    def match_column(cls, column_name: str, field_name: str) -> float:
        """
        Calculate match score for a column against a standardized field.

        Returns a score from 0.0 (no match) to 1.0 (perfect match).
        """
        column_lower = column_name.lower().strip()

        # Check pattern matches first
        patterns = cls.FIELD_PATTERNS.get(field_name, [])
        for pattern in patterns:
            if re.search(pattern, column_lower):
                # Give high score for pattern match
                return 0.9

        # Fallback to fuzzy string matching
        return cls.similarity_score(column_name, field_name.replace("_", " "))

    @classmethod
    def suggest_mapping(
        cls,
        columns: List[str],
        clinic_id: str,
        clinic_name: Optional[str] = None,
        required_fields: Optional[List[str]] = None,
    ) -> Tuple[ColumnMapping, Dict[str, float]]:
        """
        Suggest a column mapping based on detected column names.

        Args:
            columns: List of column names from the Excel file
            clinic_id: Unique identifier for the clinic
            clinic_name: Human-readable clinic name
            required_fields: List of fields that must be mapped

        Returns:
            Tuple of (ColumnMapping, confidence_scores)
        """
        if required_fields is None:
            # These fields are essential for a valid trip
            required_fields = [
                "patient_name",
                "medicaid_id",
                "pickup_address",
                "pickup_city",
                "pickup_zip",
                "dropoff_address",
                "dropoff_city",
                "dropoff_zip",
                "appointment_date",
            ]

        mapping_dict = {
            "clinic_id": clinic_id,
            "clinic_name": clinic_name,
        }
        confidence_scores = {}

        # For each standardized field, find the best matching column
        for field in cls.FIELD_PATTERNS.keys():
            best_column = None
            best_score = 0.0

            for column in columns:
                score = cls.match_column(column, field)
                if score > best_score:
                    best_score = score
                    best_column = column

            # Only suggest mapping if confidence is reasonable (>0.5)
            # or if it's a required field (must map something)
            if best_column and (best_score > 0.5 or field in required_fields):
                mapping_dict[field] = best_column
                confidence_scores[field] = best_score

        # Verify all required fields are mapped
        missing_required = [f for f in required_fields if f not in mapping_dict]
        if missing_required:
            # Try a second pass with lower threshold for required fields
            for field in missing_required:
                best_column = None
                best_score = 0.0

                for column in columns:
                    score = cls.match_column(column, field)
                    if score > best_score:
                        best_score = score
                        best_column = column

                if best_column and best_score > 0.0:
                    mapping_dict[field] = best_column
                    confidence_scores[field] = best_score

        mapping = ColumnMapping(**mapping_dict)
        return mapping, confidence_scores

    @classmethod
    def validate_mapping(cls, mapping: ColumnMapping, excel_columns: List[str]) -> List[str]:
        """
        Validate that a mapping references valid Excel columns.

        Returns list of error messages (empty if valid).
        """
        errors = []

        # Check that all mapped columns exist in the Excel file
        mapping_dict = mapping.model_dump()
        for field, column_name in mapping_dict.items():
            if field in ("clinic_id", "clinic_name", "created_at", "updated_at"):
                continue  # Skip metadata fields

            if column_name and column_name not in excel_columns:
                errors.append(
                    f"Mapped column '{column_name}' for field '{field}' "
                    f"not found in Excel file"
                )

        return errors

    @classmethod
    def get_unmapped_columns(
        cls,
        excel_columns: List[str],
        mapping: ColumnMapping
    ) -> List[str]:
        """
        Get list of Excel columns that aren't mapped to any field.

        Useful for showing user which data will be ignored.
        """
        mapped_columns = set()
        mapping_dict = mapping.model_dump()

        for field, column_name in mapping_dict.items():
            if column_name and isinstance(column_name, str):
                mapped_columns.add(column_name)

        return [col for col in excel_columns if col not in mapped_columns]
